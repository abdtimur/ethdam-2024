# from langchain_community.document_loaders import WebBaseLoader
import bs4
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader, JSONLoader
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

import json
from pathlib import Path
from pprint import pprint


# Load environment variables from .env file
load_dotenv()

llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
prompt = hub.pull("rlm/rag-prompt")

# file_path='../../data/datectors.json'
# data = json.loads(Path(file_path).read_text())
                  
# Load, chunk and index the contents of the blog.
# loader = WebBaseLoader(
#     web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
#     bs_kwargs=dict(
#         parse_only=bs4.SoupStrainer(
#             class_=("post-content", "post-title", "post-header")
#         )
#     ),
# )
loader = JSONLoader(
    file_path='data/detectors.json',
    jq_schema='.detectors[]',
    text_content=False)
docs = loader.load()
print(f'Loaded {len(docs)} documents')

# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
# splits = text_splitter.split_documents(docs)
vectorstore = Chroma.from_documents(documents=docs, embedding=OpenAIEmbeddings())

# Retrieve and generate using the relevant snippets of the blog.
retriever = vectorstore.as_retriever()
prompt = hub.pull("rlm/rag-prompt")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

res = rag_chain.invoke("What decoder should be used to verify unused variables?")

print(res)

vectorstore.delete_collection()