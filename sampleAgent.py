# sample project 
#first Langchain Example 
# Install
# Create a tool
#create a GEMINI LLM
# Ask qurstion

import os
from langchain_google_genai import GoogleGenerativeAI, ChatGoogleGenerativeAI
from langchain.agents.factory import create_agent as create_langchain_agent
import logging
from langchain.tools import tool

logging.basicConfig(level=logging.INFO)

# add a docstriung to the ine below to explain what the function does
@tool#("multiply", return_direct=True)
# This tool takes three integers as input and returns their product plus the third integer.
# The @tool decorator registers this function as a tool that can be used by the agent.

def multiply_tool(a: int, b: int, c: int) -> int:
    """Multiply two numbers and add a third number to the result."""
    return a * b + c
tools = [multiply_tool]

def create_gemini_llm():
    # Create a Gemini LLM instance
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    
    return llm

def create_agent(llm):

    tools = [multiply_tool]
    # Create an agent with the specified LLM and tools
    agent = create_langchain_agent(llm, tools, debug=True)
    return agent

def main():
    # Set up the Gemini LLM
    llm = create_gemini_llm()
    # Create the agent
    agent = create_agent(llm)
    # Ask a question to the agent
    question = input("Enter the digits: ") # example question that uses the multiply_tool
    answer = agent.invoke(
        {"messages": [{"role": "user", "content": question}]}
    )
    
    print(f"Answer: {answer}")  

if __name__ == "__main__":
    main()