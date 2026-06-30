# in this we will use Pydantic
# to cerate user record
# by using tool

import os
import logging
import time
from langchain_core import tools
from langchain.agents.factory import create_agent as create_langchain_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

#configuring logging
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # this configures the logging system to log messages with a specific format that includes the timestamp, log level, and message content
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

logger = logging.getLogger(__name__) 
#create a file handler and a console handler for logging
file_handler = logging.FileHandler('16_record_tool_agent.log') 
console_handler = logging.StreamHandler()
# set the logging level for both handlers to INFO
file_handler.setLevel(logging   .INFO)
console_handler.setLevel(logging.INFO)
# create a formatter and set it for both handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
# add the handlers to the logger
#logger.addHandler(file_handler)
#logger.addHandler(console_handler)  

# now llm and GEMINI_API_KEY are same as before
def create_gemini_llm():
    try:
        logger.info("Gemini API key initialized.")
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        logger.info("Finished reading Gemini API key...")
        if not GEMINI_API_KEY:
                 logger.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
                 raise ValueError("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")

        logger.info("Creating Gemini LLM instance...")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        logger.info("Gemini LLM created successfully.")
    except Exception as e:
        logger.error(f"Error creating Gemini LLM instance: {e}")
        raise e
    logger.info("Started reading Gemini API key...") 
    return llm

# lets crate a schema for user record using pydantic
class CustomerInput(BaseModel):
    name: str = Field(
         description="The name of the user"
         ) # this defines a field for the user's name with a description
    city: str = Field(
         description="The city of residence of the user"
         ) # this defines a field for the user's city of residence with a description
    age: int = Field(
         description="The age of the user"
         ) # this defines a field for the user's age with a description
    country: str = Field(
         description="The country of residence of the user"
         ) # this defines a field for the user's country of residence with a description
    # you can add more fields as needed, such as occupation, interests, etc.

#now creat tools for creating user record and getting user record
@tools.tool(args_schema=CustomerInput) # this decorator registers the function as a tool and specifies that it expects arguments that match the UserRecord schema
def create_user_record(
     name: str,
     city: str,
     age: int,
     country: str):
    """Create a user record with the provided name, city, age, and country, and return the record."""
    f"TOOL CALLED -> create_user_record | "
    f"name={name}, age={age}, city={city}, country={country}"

    return {
         "Name": {name},
         "City ":  {city },
         " age" : {age},
         " country": {country}
    }# this returns the provided user record

def create_agent(llm):
    """
    Create an agent with the specified LLM and tools.
    This function defines the tools that the agent can use and creates the agent using the provided LLM and tools.
    """
    tools = [create_user_record] # this defines a list of tools that the agent can use
    logger.info("Creating agent with tools...") # this logs an informational message indicating that the agent is being created
    agent = create_langchain_agent(model= llm, tools = tools) # this creates an agent using the specified LLM and tools
    logger.info("Agent created successfully.") # this logs an informational message indicating that the agent has been created successfully
    return agent # this returns the created agent   

def main():
    logger.info("\n...inside the main process...") # this logs an informational message indicating that the agent creation process is starting
    llm = create_gemini_llm() 
    logger.info("\n...creating agent...") # this logs an informational message indicating that the agent is being created
    agent = create_agent(llm) 
    logger.info("\n...invoking agent...") # this logs an informational message indicating that the agent is being invoked
    question = input(" user : ")
    answer = agent.invoke(
          {"messages": [{"role": "user", "content": question}]}
    )
    final_answer = answer["messages"][-1].content
    logger.info(f"\n...answer received...") # this logs an informational message indicating that the answer has been received
    print(final_answer)

if __name__ == "__main__":
    main() # this calls the main function to execute the program
