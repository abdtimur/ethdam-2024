
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

address = '0xdac17f958d2ee523a2206206994597c13d831ec7'
query = 'I want to mint USDT tokens, is it safe?' 

slither = Slither(address, etherscan_api_key=os.getenv('ETHERSCAN_API_KEY'))
detectors_all = [getattr(all_detectors, name) for name in dir(all_detectors)]
detectors_all = [d for d in detectors_all if inspect.isclass(d) and issubclass(d, AbstractDetector)]
detectors_arguments = [d.ARGUMENT for d in detectors_all]
source_code = slither.source_code
print('Getting detectors required for the contract...')

llm = ChatOpenAI(model="gpt-3.5-turbo-0125")

loader = JSONLoader(
file_path='data/detectors.json',
jq_schema='.detectors[]',
text_content=False)
docs = loader.load()
print(f'Loaded {len(docs)} documents')

vectorstore = Chroma.from_documents(documents=docs, embedding=OpenAIEmbeddings())

retriever = vectorstore.as_retriever()
prompt = ChatPromptTemplate.from_template("""
        You need to do a rough analysis of the contract code to figure out which detectors to run.
        In the content below, you will find the list of available detectors to be activated for security checks.
        Be precise and provide the list of detectors required to run on the contract.
        Return ONLY the argument of the detectors required, they should be comma separated. DO NOT include any additional information in the response.
        Operate ONLY with the argument names from the provided context, do not any additional information or not in the list argument names.
        Few question - answer pairs examples:
        Q: What detectors should I run?
        A: uninitialized_storage_slot, uninitialized_local_variable


        <context>
        {context}
        </context>
        <source_code>
        {source_code}
        </source_code>
        Question: {input}
    """)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
docs_sorted = retriever | format_docs
rag_chain = (
   prompt
    | llm
    | StrOutputParser()
)

res = rag_chain.invoke({"input": query, "source_code": source_code, "context": docs_sorted})

res = res.split(',')
print(f'Detectors required: {res}')
detectors = [d.strip() for d in res]
print(f'Detectors required: {detectors}')
print(f'Filter Arguments: {detectors_arguments}')
filtered_detectors = [d for d in detectors if d in detectors_arguments]

print(f'Detectors required: {filtered_detectors}')
