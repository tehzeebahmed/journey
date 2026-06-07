# Student registration form using Pydantic
# This code defines a Pydantic model for a student registration form, which includes fields for
# name, city, age, email, country and a auto generated student ID
# . Each field has a description for better documentation and validation.

import os
from turtle import st
from urllib import response
from pydantic import BaseModel, Field, EmailStr
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent as create_langchain_agent
from langchain_core import tools
import logging
from datetime import datetime
import json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
File_handler = logging.FileHandler('18_pydantic_agent_JSON.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
File_handler.setFormatter(formatter)
logger.addHandler(File_handler)

def create_gemini_llm():
    logger.info("Reading GEMINI API KEY...") 
    api_key = os.getenv("GEMINI_API_KEY")
    #env file should be named as .env and should be in the same directory as the script.
    if not api_key:
            logger.error("GEMINI API KEY not found. Please set the GEMINI_API_KEY environment variable.")
            raise ValueError("GEMINI API KEY not found. Please set the GEMINI_API_KEY environment variable.")
    else:
            logger.info("GEMINI API KEY successfully read from environment variable.")
    logger.info("Creating Gemini LLM...") 
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7
        )
    return llm

class StudentRegistration(BaseModel):
    student_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        # explaination: This field is a unique identifier for the student, 
        # which is automatically generated using the uuid library. 
        # The default_factory parameter is used to specify that a new UUID should be generated each time a new instance of the StudentRegistration model is created.
        description="A unique identifier for the student, auto-generated as a UUID"
    )
    name: str = Field(
        description="The full name of the student"
    )
    city: str = Field(
        description="The city where the student resides"
    )
    age: int = Field(
        ge=3, le=25, # this sets the minimum and maximum age for the student to be between 3 and 25 years old
        description="The age of the student between 3 and 25 years old"
    )
    grade: str = Field(
        description="The grade of the student"
    )
    email: EmailStr = Field(
        description="The email address of the student"
    )
    country: str = Field(
        description="The country where the student resides"
    )
    
    #now create a tool to save the student record in a JSON file
@tools.tool(args_schema=StudentRegistration)
#docstring for the tool
def save_student_record(
    student_id: str,
    name: str,
    city: str,
    age: int,
    grade: str,
    email: EmailStr,
    country: str
):

    """This tool saves a student record to a JSON file.  
    It takes the student's name, city, age, email, and country as input, 
    generates a unique student ID, and saves the record along with a timestamp 
    to a file named '18_student_records.json'. If the file already exists, 
    it loads the existing records, appends the new record, and saves it back to the file."""

    print("******** TOOL EXECUTED ********")

    student_record = {
        "student_id": student_id,
        "name": name,
        "city": city,
        "age": age,
        "grade": grade,
        "email": email,
        "country": country,
        "created_at": datetime.now().isoformat()
    }

    logger.info(f"using tool -> save_student_record for {os.name}...")
    print(f"using tool -> save_student_record for {name}...")
    logger.info(f"Saving student record for {os.name}...")
    file_name = '18_student_records.json'
    # 1. initiate the empty list to hold the records
    records = []
    # 2. If the file already exists and has data, load it first
    if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
        with open(file_name, 'r') as file:
            try:
                records = json.load(file)   
                logging.Logger.info(f"Loaded existing records from {file_name}.")
            except json.JSONDecodeError:
                logging.Logger.warning(f"Existing file {file_name} is empty or corrupted. Starting with an empty list.")
                records = []
    # 3. Append the new student record to the list
    records.append(student_record)
    # 4. Save the updated list back to the JSON file
    with open(file_name, 'w') as file:
        json.dump(records, file, indent=4)
        logger.info(f"Student record for {name} saved to {file_name}.")         
    
    return {
         "status": "success",
         "message": "Student record created",
         "record": student_record
         }

def main():
    logger.info("\n...inside the main process...") # this logs an informational message indicating that the agent creation process is starting
    try:
        llm = create_gemini_llm()
    except Exception as e:
        logger.error(f"Error creating Gemini LLM instance: {e}")
        raise e
    logger.info("Gemini LLM instance created successfully.") # this logs an informational message indicating that the Gemini LLM instance has been created successfully
    logger.info("Creating agent with tools...") # this logs an informational message indicating that the agent creation process is starting
    agent = create_langchain_agent(
         model=llm, 
         tools=[save_student_record]
         ) # this creates an agent using the create_langchain_agent function, passing in the Gemini LLM instance and a list of tools (in this case, just the save_student_record tool)
    logger.info("Agent created successfully with tools.") # this logs an informational message indicating that the agent has been created successfully with the specified tools
    return agent
if __name__ == "__main__":
    agent = main()
    logger.info("\n...invoking agent...") # this logs an informational message indicating that the agent is being invoked
    question = input(" user : ")
    answer = agent.invoke(
          {"messages": [{"role": "user", "content": question}]}
    )
    final_answer = answer["messages"][-1].content
    logger.info(f"\n...answer received...") # this logs an informational message indicating that the answer has been received
    print(final_answer)
    print("\n\nAgent response:", answer)
