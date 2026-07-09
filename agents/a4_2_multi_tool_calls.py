"""
this is another attenpt for calling tools 
1) multiply for two numbers
2) addition of thwo numbers  
3) Square of the result 
"""

import os
import config
import json
from llm_router import chat
from openai import OpenAI
from tee_logger import start_tee, stop_tee

# GEMINI_API = os.getenv("GEMINI_API_KEY")
# G_BASE_URL = os.getenv("GEMINI_BASE_URL")
# G_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")

GEMINI_API = os.getenv("MISTRAL_API_KEY")
G_BASE_URL = os.getenv("MISTRAL_BASE_URL")
G_MODEL_NAME = os.getenv("MISTRAL_MODEL_NAME")


SYSTEM_PROMPT = SYSTEM_PROMPT = """You are a calculator assistant. 
You MUST use the available tools for ALL calculations, no matter how simple.
NEVER calculate in your head. ALWAYS call a tool.
Even for basic arithmetic like 1+1, you must use the add_numbers tool."""

client = OpenAI(api_key=GEMINI_API, base_url=G_BASE_URL)
# *********************************************************************
# Define the three tools that LLM can call with the strict JSON Schema
# Strict Schemas prevetns unexpected inputs (secutrity best practices)
# *********************************************************************

#tool 1 add numbers
ADD_NUMBERS = {
    "type": "function",     
    "function": {
        "name": "add_numbers",
        "description": "It adds two numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "first number supplied by user for additon operation"
                },
                "b":{
                    "type": "integer",
                    "description": "Second number provided by user for additioon"
                }
            },
            "required":["a", "b"],
            "additionalProperties": False
        }
    }
}
MULTIPLY_NUMBERS = {
    "type": "function",
    "function": {
        "name": "multiply_numbers",
        "description": " It reurns multiple of twoi digits supplied by user",
        "parameters":{
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": " first Number supplied by the user for Multiplication"
                },
                "b": {
                    "type": "integer",
                    "description": "Second number supplied by user for Multiplication"
                }
            },
            "required": ["a", "b"],
            "additionalProperties": False
        }
    }
}
SQUARE_RESULTS = {
    "type": "function",
    "function": {
        "name": "square_result",
        "description": "It multiply number provided by result to same number",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "it is a integer numbner to be multiplied by itself"
                }
            },
            "required": ["a"],
            "additionalProperties": False
        }
    }
}
# combine all tools into a Single List for easy passing to LLM
AVAILABLE_FUNCTIONS = [ADD_NUMBERS, MULTIPLY_NUMBERS, SQUARE_RESULTS]

def add_numbers(a: int, b:int) -> int:
    "add two numbers and return result"
    return a + b

def multiply_numbers(a: int, b: int) -> int:
    "multiply two digits provided as arguments in function call"
    return a * b

def square_result(a: int) -> int:
    " it  multiply number with the number itself"
    return a * a

# Tool despatcher
def tool_call_despatcher(tool_name: str, tool_args: dict) -> str:
    """Calls the right function based on what LLM requested."""
    if tool_name == "add_numbers":
        return (add_numbers(**tool_args))
    elif tool_name == "multiply_numbers":
        return (multiply_numbers(**tool_args))
    elif tool_name == "square_result":
        return (square_result(**tool_args))
    else:
        return ("Invalid Tool Name")
    
def run_agent(user_query: str) -> str:
    """
        Full agent loop:                              
        1. Send query to LLM with tools
        2. LLM decides which tool to call
        3. We run the tool and get DB results
        4. Send results back to LLM
        5. LLM gives final natural language answer
        """
    print('-' * 60)
    print(f"user Query : -  {user_query}")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    # keep looping until LLM stops calling tools
    while True: # need for keep running llm for other parts of query
        response = client.chat.completions.create(
            model=G_MODEL_NAME,
            messages=messages, tools=AVAILABLE_FUNCTIONS, tool_choice="auto")  # ← LLM MUST call a tool, no direct answers allowed
        
        reply = response.choices[0].message
        if reply.tool_calls:
            messages.append(reply)
            for i in reply.tool_calls:
                tool_name = i.function.name
                tool_args = json.loads(i.function.arguments)
                tool_results = tool_call_despatcher(tool_name, tool_args)
                print(f"\n [Tool Name] -> {tool_name} - [tool Result] -> {tool_results}")

                messages.append(
                    { "role": "tool", "tool_call_id": i.id, "content": str(tool_results)}
                )
                # NO return here — loop back to top naturally
        else:
            return reply.content   # LLM has no more tools to call — this is the final answer

def main ():
    print('-' * 60)
    tee = start_tee(__file__)
    user_query = input(f" Enter your query here : ")
    answer = run_agent(user_query)
    print(answer)
    stop_tee(tee)

if __name__ == '__main__':
    main()
                       
