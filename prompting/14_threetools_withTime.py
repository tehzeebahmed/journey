
# LLM model how it workd display
# This code is a simple representation of how a Large Language Model (LLM) works.
# It takes an input prompt, processes it, and generates a response based on the learned patterns


import os # this module provides a way of using operating system dependent functionality
import random # this module implements pseudo-random number generators for various distributions
import time # this module provides various time-related functions

from langchain_google_genai import ChatGoogleGenerativeAI # this module provides a way to interact with Google's Generative AI models
from langchain.agents.factory import create_agent as create_langchain_agent

from langchain_core import tools # this module provides a way to define tools that can be used by the agent
import logging # this module provides a way to log messages for debugging and monitoring purposes

def setup_logging():
    """
    Set up logging for the application.
    This function configures the logging settings, including log level, format, and handlers.
    """
    # Set up logging
    
logging.basicConfig(level=logging.INFO) # this sets the logging level to INFO, which means that all messages at this level and above will be logged
logger = logging.getLogger(__name__) # this creates a logger object that can be used to log messages in this module
# crate file and console handlers
file_handler = logging.FileHandler('llm_model.log') # this creates a file handler that will write log messages to a file named 'llm_model.log'
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

logger.info("getting Gemini API key.....") # this logs an informational message indicating that the agent is being set up
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # this retrieves the Gemini API key from the environment variables
if not GEMINI_API_KEY: # this checks if the Gemini API key is not found in the environment variables
    logger.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.") # this logs an error message indicating that the Gemini API key was not found
    raise ValueError("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.") # this raises a ValueError indicating that the Gemini API key was not found


def initiate_llm():
    """
    Initiate the Large Language Model (LLM) and set up the necessary configurations.
    This function initializes the LLM, sets up the agent, and prepares it for processing input prompts.
    """

    # Initialize the LLM
    logger.info("Initializing the Large Language Model (LLM)...") # this logs an informational message indicating that the LLM is being initialized
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    logger.info("LLM initialized successfully.") # this logs an informational message indicating that the LLM has been initialized successfully

    return llm


@tools.tool
def get_current_time():
    """
    Get the current time.
    This function returns the current time in a human-readable format.
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) # this returns the current time formatted as a string in the format "YYYY-MM-DD HH:MM:SS"

@tools.tool
def add_numbers(a: int, b: int) -> int:
    """
    Add two numbers.
    This function takes two integers as input and returns their sum.
    """
    return a + b # this returns the sum of the two input integers

@tools.tool
def multiply_numbers(a: int, b: int) -> int:
    """
    Multiply two numbers.
    This function takes two integers as input and returns their product.
    """
    return a * b # this returns the product of the two input integers

def create_agent_with_tools(llm):
    """
    Create an agent with the specified tools.
    This function creates an agent that can use the defined tools to perform tasks based on natural language input.
    """
    tools = [get_current_time, add_numbers, multiply_numbers] # this defines a list of tools that the agent can use
    logger.info("Creating agent with tools...") # this logs an informational message indicating that the agent is being created
    agent = create_langchain_agent(llm, tools) #this creates an agent using the specified LLM and tools
    logger.info("Agent created successfully.") # this logs an informational message indicating that the agent has been created successfully
    return agent

def main():
    """
    Main function to run the LLM model demonstration.
    This function initializes the LLM, creates an agent with tools, and processes a sample input prompt to demonstrate how the LLM works.
    """
    setup_logging() # this calls the setup_logging function to configure logging settings
    llm = initiate_llm() # this calls the initiate_llm function to initialize the LLM and retrieves the LLM instance
    agent = create_agent_with_tools(llm) # this calls the create_agent_with_tools function to create an agent with the specified tools and retrieves the agent instance

    # Sample input prompt for demonstration
    input_prompt = input("Enter your question: ") # this prompts the user to enter an input prompt and stores it in the variable input_prompt
    logger.info(f"Processing input prompt: {input_prompt}") # this logs an informational message indicating that the input prompt is being processed
    
    response = agent.invoke(
        {"messages": [{"role": "user", "content": input_prompt}]}
        )
    print(f"Response: {response.items()}") # this prints the response generated by the agent to the console
    # this calls the invoke method of the agent with the input prompt and stores the generated response in the variable response


    logger.info(f"Response: {response}") # this logs an informational message displaying the response generated by the agent
if __name__ == "__main__":
    main() # this checks if the script is being run directly and calls the main function to execute the program