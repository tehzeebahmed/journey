# two agents problem
# tool used by agents 1) multiply 2) add
# reason, decide , act on the basis of user input
# have logging into file


import os
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
from langchain_core import tools
from langchain.agents.factory import create_agent as create_langchain_agent


#create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create a file handler
file_handler = logging.FileHandler('twotoolsagent.log')
file_handler.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger.addHandler(console_handler)

#creating two tools 
@tools.tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers and return the result."""
    return a * b

@tools.tool
def add(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b


def create_gemini_llm():
    # Create a Gemini LLM instance
    logger.info("Creating Gemini LLM instance...")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    logger.info("Gemini LLM created successfully.")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set.")

    logger.info("Gemini API key initialized.")
    return llm

#create an agent with the two tools and the Gemini LLM
def create_agent(llm):

    tools = [add, multiply]
    # Create an agent with the specified LLM and tools
    agent = create_langchain_agent(llm, tools, debug=True)
    return agent

def main():
    # Set up the Gemini LLM
    logger.info("Setting up Gemini LLM...")
    llm = create_gemini_llm()
    # Create the agent
    agent = create_agent(llm)
    # Ask a question to the agent
    question = input("Enter the digits: ") # example question that uses the multiply_tool
    answer = agent.invoke(
        {"messages": [{"role": "user", "content": question}]}
    )
    # get answer in the log file a
    # answer is messy we need to get only the content of the answer and log it
    answer = answer.__format__('') # clean up the answ
    logger.info(f"Question: {question} | \n \n Answer: {answer.content}")

    print(f"Answer: {answer.content}")

if __name__ == "__main__":
    main()
