# creating foiur agents
# 1- Add 2- Multiply 3- square of the result, 4- current time
# reason, decide , act on the basis of user input
# have logging into file    
import os
import time # this module provides various time-related functions
import logging
from urllib import response # this module provides a way to log messages for debugging and monitoring purposes
from langchain_google_genai import ChatGoogleGenerativeAI # this module provides a way to interact with Google's Generative AI models
from langchain_core import tools # this module provides a way to define tools that can be used by the agent
from langchain.agents.factory import create_agent as create_langchain_agent # this

# loggging setup
logger = logging.getLogger(__name__) # this creates a logger object that can be used to log messages in this module
logger.setLevel(logging.INFO) # this sets the logging level to INFO, which means that all messages at this level and above will be logged
# create file and console handlers
file_handler = logging.FileHandler('fourtoolsagent.log') # this creates a file handler that will write log messages to a file named 'fourtoolsagent.log'
console_handler = logging.StreamHandler() # this creates a console handler that will write log messages to the console
# set level and format for handlers
file_handler.setLevel(logging.INFO) # this sets the logging level for the file handler to INFO
console_handler.setLevel(logging.INFO) # this sets the logging level for the console handler to INFO
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') # this creates a formatter that will format log messages with the timestamp, logger name, log level, and message
file_handler.setFormatter(formatter) # this sets the formatter for the file handler
console_handler.setFormatter(formatter) # this sets the formatter for the console handler
# add handlers to logger
logger.addHandler(file_handler) # this adds the file handler to the logger
logger.addHandler(console_handler) # this adds the console handler to the logger

def create_gemini_llm():
    try:
        logger.info("Gemini API key initialized.") # this logs an informational message indicating that the Gemini API key has been initialized
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # this retrieves the Gemini API key from the environment variables
        logger.info("Finished reading Gemini API key...")
        if not GEMINI_API_KEY: # this checks if the Gemini API key is not found in the environment variables
                 logger.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.") # this logs an error message indicating that the Gemini API key was not found
                 raise ValueError("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.") # this raises a ValueError indicating that the Gemini API key was not found

        logger.info("Creating Gemini LLM instance...") # this logs an informational message indicating that the Gemini LLM instance is being created
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0) # this creates an instance of the ChatGoogleGenerativeAI class with the specified model and temperature settings
        logger.info("Gemini LLM created successfully.") # this logs an informational message indicating that the Gemini LLM instance has been created successfully
    except Exception as e:
        logger.error(f"Error creating Gemini LLM instance: {e}") # this logs an error message if there was an issue creating the Gemini LLM instance
        raise e # this re-raises the exception to be handled by the caller
    logger.info("Started reading Gemini API key...") 
    return llm

@tools.tool
def add(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    print("TOOL CALLED -> Add")
    return a + b

@tools.tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers and return the result."""
    print("TOOL CALLED -> Multiply")
    return a * b

@tools.tool
def square(number: int) -> int:
    """Calculate the square of a number and return the result."""
    print("TOOL CALLED -> square")
    return number * number

@tools.tool
def get_current_time() ->str:
    """Get the current time in a human-readable format."""
    print("TOOL CALLED -> get_current_time")
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def create_agent(llm):
    """
    Create an agent with the specified LLM and tools.
    This function defines the tools that the agent can use and creates the agent using the provided LLM and tools.
    """
    tools = [add, 
             multiply, 
             square, 
             get_current_time
             ] # this defines a list of tools that the agent can use
    logger.info("Creating agent with tools...") # this logs an informational message indicating that the agent is being created
    agent = create_langchain_agent(model= llm, tools = tools) # this creates an agent using the specified LLM and tools
    logger.info("Agent created successfully.") # this logs an informational message indicating that the agent has been created successfully
    return agent

def main():
    """
    Main function to set up the Gemini LLM and create the agent.
    This function initializes the Gemini LLM and creates an agent that can use the defined tools to perform tasks based on natural language input.
    """
    logger.info("Setting up Gemini LLM...\n") # this logs an informational message indicating that the Gemini LLM is being set up
    llm = create_gemini_llm() # this calls the function to create the Gemini LLM instance
    logger.info(" agent setup completed ...\n") # this logs an informational message indicating that the agent is being created
    logger.info("now Creating agent...\n") # this logs an informational message indicating that the agent is being created
    agent = create_agent(llm) # this calls the function to create the agent using the initialized LLM
    question = input("\n\nEnter the digits: ") # this prompts the user to enter a question that may involve using the defined tools
    answer = agent.invoke(
        {"messages": [{"role": "user", "content": question}]}
    ) # this calls the invoke method of the agent with the user's question and stores the generated answer in the variable answer
    final_answer = answer["messages"][-1].content
    logger.info(f"Question: {question} | \n \n Answer: {final_answer}") # this logs an informational message displaying the user's question and the agent's answer
    print(f"Answer: {final_answer}") # this prints the agent's answer to the console

if __name__ == "__main__":
    main() # this calls the main function to execute the program
    