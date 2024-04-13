from langchain_core.tools import tool
from slither import Slither
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import JSONLoader
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from slither.detectors import all_detectors
from slither.detectors.abstract_detector import AbstractDetector

import os
import inspect
import json

from .tool_type import ToolType

@tool
def initiate_detectors_check(address: str, query: str) -> dict:
    """
    This function will perform initial analysis of the contract at the given address and identify the list of detectors required to run on the contract.
    As the second argument, you should provide the initial query from the user.
    Address should be in the 0x format and should be a valid contract address.
    It will also run security checks on the contract to identify any potential security vulnerabilities and return the list of results.
    You should use this function to initiate the security checks on the contract, if user is at ris
    """
    print(f"Decided to initiate detectors check for address: {address}. Query: {query}")

    # Check that address is a valid 0x contract address
    if not address.startswith('0x') or len(address) != 42 or address == '0x1234567890123456789012345678901234567890':
        return {
            "type": ToolType.DETECTORS_CHECK,
            "detectors_checks": [],
            "source_code": None
        }
    
    try:
        slither = Slither(address, etherscan_api_key=os.getenv('ETHERSCAN_API_KEY'))
    except Exception as e:
        print(f"Error getting contract at address: {address}. Error: {e}")
        return {
            "type": ToolType.DETECTORS_CHECK,
            "detectors_checks": [],
            "source_code": None
        }
    
    detectors_all = [getattr(all_detectors, name) for name in dir(all_detectors)]
    detectors_all = [d for d in detectors_all if inspect.isclass(d) and issubclass(d, AbstractDetector)]
    detectors_arguments = [d.ARGUMENT for d in detectors_all]
    source_code = slither.source_code
    print('Getting detectors required for the contract...')

    loader = JSONLoader(
    file_path='data/detectors.json',
    jq_schema='.detectors[]',
    text_content=False)
    docs = loader.load()
    #print(f'Loaded documents: {docs}')

    vectorstore = Chroma.from_documents(documents=docs, embedding=OpenAIEmbeddings())

    retriever = vectorstore.as_retriever()
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    selected_docs = retriever.get_relevant_documents(query)
    #print(f'Selected detectors docs: {len(docs)}. Running detectors on the contract...')
    #print(f'Detectors required: {selected_docs}')
    parsed_detectors = [json.loads(doc.page_content) for doc in selected_docs]
    #print(f'Parsed detectors: {parsed_detectors}')

    detectors_arguments = [d['argument'] for d in parsed_detectors]
    print(f'Detectors arguments: {detectors_arguments}')
    selected_detectors = [d for d in detectors_all if d.ARGUMENT in detectors_arguments]
    print(f'Selected detectors: {selected_detectors}')

    for detector in selected_detectors:
        slither.register_detector(detector)

    results = slither.run_detectors()
    
    final_data = []
    # Assuming `selected_detectors` and `results` are already defined and aligned by index
    for i, detector in enumerate(selected_detectors):
        corresponding_result = results[i]  # Directly access the result by index
        if len(corresponding_result) > 0:
            # Assuming corresponding_result is a dictionary and you want to print some info
            print(f"Detector {detector.ARGUMENT} - Results: {len(corresponding_result)}")
            final_data.append({
                "detector_id": detector.ARGUMENT,
                "detector_info": _transform_detector(detector),
                "detector_check_result": [_transform_result(result) for result in corresponding_result]
            })
        else:
            # Handle the case where the result is an empty list or None
            print(f"Detector {detector.ARGUMENT} - No results found")
            final_data.append({
                "detector_id": detector.ARGUMENT,
                "detector_info": _transform_detector(detector),
                "detector_check_result": []
            })
    print(f"Final data: {final_data}")
    vectorstore.delete_collection()

    return {
        "type": ToolType.DETECTORS_CHECK,
        "detectors_checks": final_data,
        "source_code": source_code
    }

@tool
def mint_check(address: str) -> dict:
    """
    This function checks if the contract at the given address overrides the _mint function. So it is a mint check which only applies to tokens that have a mint function.
    """
    slither = Slither(address, etherscan_api_key=os.getenv('ETHERSCAN_API_KEY'))
    source_code = slither.source_code
    target = slither.compilation_units[0]
    print('Checking mint function in the contract')

    # Iterate over all the contracts
    for contract in target.contracts:
        # If the contract is derived from MyContract
        if target in contract.inheritance:
            # Get the function definition  
            mint = contract.get_function_from_signature('_mint(address,uint256)')
            # If the function was not declared by coin, there is a bug !
            # Detect error only for contracts overriding the '_mint' function
            if mint.contract_declarer == contract:
                return {
                    "type": ToolType.MINT_CHECK,
                    "result": f'Slither Check Result -> Error: {contract.name} overrides the _mint function',
                }
    return {
        "type": ToolType.MINT_CHECK,
        "result": 'Slither Check Result -> All good!',
    }

@tool
def unprotected_func(address: str) -> dict:
    """
    This function checks if the contract at the given address has any unprotected functions. 
    It checks if the contract has any public or external functions that are not protected by the onlyOwner modifier.
    """
    slither = Slither(address, etherscan_api_key=os.getenv('ETHERSCAN_API_KEY'))
    source_code = slither.source_code

    whitelist = ['balanceOf(address)']
    print('Checking unprotected functions in the contract')

    for contract in slither.contracts:
        for function in contract.functions:
            if function.full_name in whitelist:
                continue
            if function.is_constructor:
                continue
            if function.visibility in ['public', 'external']:
                if not 'onlyOwner()' in [m.full_name for m in function.modifiers]:
                    return {
                        "type": ToolType.UNPROTECTED_FUNC,
                        "result": f'Slither Check Result -> Error: {function.full_name} is unprotected',
                    }
    return {
        "type": ToolType.UNPROTECTED_FUNC,
        "result": 'Slither Check Result -> All good!',
    }

@tool
def skip_security_checks() -> dict:
    """
    This function is used to skip security checks. 
    It is used to skip security checks for the contract at the given address if there is no need to run any decoders.
    """
    print('Skipping security checks')
    return {
        "type": ToolType.SKIP_SECURITY_CHECKS,
        "result": "Security checks skipped."
    }

def get_tools():
    return [initiate_detectors_check, mint_check, unprotected_func, skip_security_checks]

def _transform_detector(detector):
    transformed = {
        #"key": detector.KEY,
        "argument": str(detector.ARGUMENT),
        "help": str(detector.HELP),
        "impact": str(detector.IMPACT),
        "confidence": str(detector.CONFIDENCE),
        "wiki": str(detector.WIKI),
        "wiki_title": str(detector.WIKI_TITLE),
        "wiki_description": str(detector.WIKI_DESCRIPTION),
        "wiki_exploit_scenario": str(detector.WIKI_EXPLOIT_SCENARIO),
        "wiki_recommendation": str(detector.WIKI_RECOMMENDATION)
    }
    return transformed

def _transform_result(data):
    transformed = {
        "check": data["check"],
        "impact": data["impact"],
        "confidence": data["confidence"],
        "description": data["description"],
        "elements": [_parse_element(el) for el in data["elements"]]
    }
    return transformed

def _parse_element(element):
    parsed = {
        "type": element["type"],
        "name": element["name"]
    }

    has_specific_fields = (
        "type_specific_fields" in element and 
        element["type_specific_fields"] is not None and 
        "parent" in element["type_specific_fields"] and 
        element["type_specific_fields"]["parent"] is not None)

    # if element has specific fields to save
    if has_specific_fields:
        parsed["type_specific_fields"] = {
            "parent": {
                "type": element["type_specific_fields"]["parent"]["type"],
                "name": element["type_specific_fields"]["parent"]["name"]
            }
        }
    return parsed