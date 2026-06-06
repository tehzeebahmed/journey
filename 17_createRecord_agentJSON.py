#using Pydantic 
# we will cerate a record based on user input and 
#save it in JSON file
# User → Gemini Agent → Pydantic Validation → Tool Calling → JSON Persistence → Logging → Final Response

import json
import os
from datetime import datetime
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core import tools
from langchain.agents import create_agent as create_langchain_agent
from pydantic import BaseModel, Field

#logging details setup
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

logger=logging.getLogger(__name__)

#create file and console Handler
file_handler = logging.FileHandler('17_create_JSON_record.log')
console_handler = logging.StreamHandler()
format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(format)
console_handler.setFormatter(format)

#now initiate llm and API key
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
    #now create tool to create record and save in JSON file
@tools.tool(args_schema=CustomerInput)
def create_user_record(
      name: str,
      city: str,
      age: int,
       country: str):
     """Create a user record with the provided name, city, age, and country, and return the record."""
     logger.info(f"TOOL CALLED -> create_user_record | "
                 f"Name: {name}, City: {city}, Age: {age}, Country: {country}"
                 ) # this logs
     print("lets see the type of create_user_record:", type(create_user_record))
     user_record = {
          "Name": name,
          "City": city,
          "Age": age,
          "Country": country,
        "created_at": datetime.now().isoformat()
     }
     logger.info(f"User record created: {user_record}") # this logs the created user
     file_name = f"17_user_record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
     if os.path.exists(file_name):
         
         logger.warning(f"File {file_name} already exists. It will be overwritten.")
         with open(file_name, 'r') as f:
              records = json.load(f)
     else:
          records = []
          records.append(user_record)
          with open(file_name, 'w') as f:
               json.dump(records, f, indent=4)
               logger.info(f"User record saved to {file_name}") # this logs that the user record has been saved to a JSON file        
          return {
               "status": "success",
               "message": "User record created",
               "record": user_record
               }

def main():
    logger.info("\n...inside the main process...") # this logs an informational message indicating that the agent creation process is starting
    llm = create_gemini_llm() 
    logger.info("\n...creating agent...") # this logs an informational message indicating that the agent is being created
    agent = create_langchain_agent(
         model=llm,
         tools=[create_user_record]
         )
          
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

             
