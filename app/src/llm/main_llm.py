import json
from operator import itemgetter
from typing import Union

from langchain.output_parsers import JsonOutputToolsParser
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    Runnable,
    RunnableLambda,
    RunnableMap,
    RunnablePassthrough,
)

from langchain import hub
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .llm_tools import get_tools

class StringRunnable(Runnable):
    def __init__(self, dict):
        self.text = json.dumps(dict)

    def run(self, input=None):
        # Optionally, use 'input' to modify 'text' or just return 'text'
        return self.text

class MainLlm():
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
        self.prompt = "You are a software engineer working on a project. You have a problem and you need to solve it. You have a set of tools at your disposal. You need to figure out which tool to use"
        tools = get_tools()
        self.llm = self.llm.bind_tools(tools)
        self.tool_map = {tool.name: tool for tool in tools}
        self.call_tool_list = RunnableLambda(self._call_tool).map()
        self.chain = self.llm | JsonOutputToolsParser() | self.call_tool_list

    def call(self, query) -> str:
        print(f"Calling with query: {query}")
        callResult = self.chain.invoke(query)
        print(f"Result Before: {callResult}")

        llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
        prompt = ChatPromptTemplate.from_template("""
            Be friendly crypto bro, who is a world class expert in blockchain and smart contract security. 
            You are helping a crypto newbie to answer a question about smart contract security. 
            Use your expertise and context to provide a detailed and informative answer.
            Below is the context derived from the tool invocation, it has analysis details and source code.
            <context>
            {context}
            </context>
            Question: {input}
        """)
        rag_chain = (
            prompt
            | llm
            | StrOutputParser()
        )
        res = rag_chain.invoke({"input": query, "context": callResult})
        print(f"Result: {res}")
        return res

    def _call_tool(self, tool_invocation: dict) -> Union[str, Runnable]:
        """Function for dynamically constructing the end of the chain based on the model-selected tool."""
        tool = self.tool_map[tool_invocation["type"]]
        return RunnablePassthrough.assign(output=itemgetter("args") | tool)
