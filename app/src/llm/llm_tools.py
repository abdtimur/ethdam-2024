from langchain_core.tools import tool
from slither import Slither

import os

@tool
def get_slither_object(address: str) -> Slither:
    """Returns the Slither object for the given address. 
    It is used as an entry function to obtain contract information, if you have an address to analyze.
    You should call this function and obtaint a Slither object before calling other tools."""
    # TODO: check if the address is a valid contract address
    slither = Slither(address, etherscan_api_key=os.getenv('ETHERSCAN_API_KEY'))
    return slither

@tool
def run_general_detectors(slither: Slither, detectors) -> dict:
    """
    You should only call this function after calling get_slither_object.
    You should pass the Slither object obtained from get_slither_object as an argument to this function.
    This function runs general detectors on the contract at the given address.
    """
    slither = Slither(slither, etherscan_api_key=os.getenv('ETHERSCAN_API_KEY'))
    source_code = slither.source_code
    print('Running general detectors on the contract')

    # TODO: load only the detectors that are passed as an argument

    # Run all the detectors
    results = slither.run_detectors()
    print(results)

    # If there are any errors, return them
    errors = [error for error in results if error.severity == 'error']
    if errors:
        return {
            "result": f'Slither Check Result -> Error: {errors[0].message}',
            "source_code": source_code
        }
    return {
        "result": 'Slither Check Result -> All good!',
        "source_code": source_code
    }

@tool
def mint_check(slither: Slither) -> dict:
    """
    You should only call this function after calling get_slither_object.
    You should pass the Slither object obtained from get_slither_object as an argument to this function.
    This function checks if the contract at the given address overrides the _mint function. So it is a mint check which only applies to tokens that have a mint function.
    """
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
                    "result": f'Slither Check Result -> Error: {contract.name} overrides the _mint function',
                    "source_code": source_code
                }
    return {
        "result": 'Slither Check Result -> All good!',
        "source_code": source_code
    }

@tool
def unprotected_func(slither: Slither) -> dict:
    """
    You should only call this function after calling get_slither_object.
    You should pass the Slither object obtained from get_slither_object as an argument to this function.
    This function checks if the contract at the given address has any unprotected functions. 
    It checks if the contract has any public or external functions that are not protected by the onlyOwner modifier.
    """
    slither = Slither(slither, etherscan_api_key=os.getenv('ETHERSCAN_API_KEY'))
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
                        "result": f'Slither Check Result -> Error: {function.full_name} is unprotected',
                        "source_code": source_code
                    }
    return {
        "result": 'Slither Check Result -> All good!',
        "source_code": source_code
    }

def get_tools():
    return [mint_check, unprotected_func]