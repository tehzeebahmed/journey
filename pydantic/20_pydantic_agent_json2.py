
"""
creating employee record and checking first if that employee exist or not
if exist then update the record otherwise create a new record
by using pydantic model , GEMINI API KEY , Agent and json file to store the records
"""

import email
import email
import os
import json
import logging
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent as create_langchain_agent
from langchain_core import tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
File_handler = logging.FileHandler('20_pydantic_agent_json2.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
File_handler.setFormatter(formatter)
logger.addHandler(File_handler)

def create_gemini_llm():
    logger.info("Reading GEMINI API KEY...") 
    print("Reading GEMINI API KEY...")
    api_key = os.getenv("GEMINI_API_KEY")
    #env file should be named as .env and should be in the same directory as the script.
    if not api_key:
            logger.error("GEMINI API KEY not found. Please set the GEMINI_API_KEY environment variable.")
            print("GEMINI API KEY not found. Please set the GEMINI_API_KEY environment variable.")
            raise ValueError("GEMINI API KEY not found. Please set the GEMINI_API_KEY environment variable.")
    else:
            logger.info("GEMINI API KEY successfully read from environment variable.")
            print("GEMINI API KEY successfully read from environment variable.")
    logger.info("Creating Gemini LLM...") 
    print("Creating Gemini LLM...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
        )
    return llm

class EmployeeRecord(BaseModel):
    name: str = Field(
        description="The full name of the employee"
    )
    city: str = Field(
        description="The city where the employee resides"
    )
    age: int = Field(
        ge=18, le=65, # this sets the minimum and maximum age for the employee to be between 18 and 65 years old
        description="The age of the employee between 18 and 65 years old"
    )
    salary: int = Field(
        ge=0, # this sets the minimum salary for the employee to be a positive number
        description="The salary of the employee"
    )
    department: str = Field(
        description="The department of the employee"
    )
    email: EmailStr = Field(
        description="The email address of the employee"
    )
    country: str = Field(
        description="The country where the employee resides"
    )

def get_next_employee_id(emailin: str = None):
    # Check if the file exists, if not create it and start with EMP0001
    if not os.path.exists("20_employee_records.json"):
        with open("20_employee_records.json", "w") as f:
            json.dump([], f)

    # Read the current counter value
    with open("20_employee_records.json", "r") as f:
        records = json.load(f)
        if records:
            email_exists = any(record['email'] == emailin for record in records)
            if email_exists:
                existing_record = next(record for record in records if record['email'] == emailin)
                logger.info(f"Employee with email {emailin} already exists. Returning existing employee ID: {existing_record['employee_id']}")
                print(f"Employee with email {emailin} already exists. Returning existing employee ID: {existing_record['employee_id']}")
                return existing_record['employee_id']
            else:
                 last_id = records[-1]['employee_id']
                 print(f"\n\nLast employee ID: {last_id}")
                 last_num = int(last_id.replace("EMP", "").replace("", ""))
                 next_num = last_num + 1
                 print(f"\n\nNext employee ID: EMP{str(next_num).zfill(4)}")
                 return f"EMP{str(next_num).zfill(4)}"
        else:
            return "EMP0001"
    
@tools.tool(args_schema=EmployeeRecord)
def create_or_update_employee(
    name : str,
    city : str,
    age : int,
    salary : int,
    department : str,
    email : EmailStr,
    country : str
):
    """Create or update an employee record, writing to a JSON file and before writing it check if it already exists then it updates the existing record else inserts it."""
    print("******** TOOL EXECUTED ********")
    employee_id = get_next_employee_id(emailin=email)
    employee_data = {
        "employee_id": employee_id,
        "name": name,
        "city": city,
        "age": age,
        "salary": salary,
        "department": department,
        "email": email,
        "country": country,
        "timestamp": datetime.now().isoformat()
    }
    # Implementation for creating or updating employee record
    logger.info(f"Creating or updating employee record for {name}...")
    print(f"Creating or updating employee record for {name}...")
    # Check if the employee record already exists in the JSON file
    if os.path.exists('20_employee_records.json'):
        with open('20_employee_records.json', 'r') as file:
            employee_records = json.load(file)
            # Check if the employee record already exists in the JSON file
            existing_record = next((record for record in employee_records 
                                    if record['employee_id'] == employee_id), None)
            if existing_record:
                 # Update the existing record
                 existing_record.update(employee_data)
                 logger.info(f"Employee record for {name} updated successfully.")
                 print(f"Employee record for {name} updated successfully.")
            else:
                 # Create a new record
                employee_records.append(employee_data)
                # Write the updated employee records back to the JSON file
                with open('20_employee_records.json', 'w') as file:
                     json.dump(employee_records, file, indent=4)
                     logger.info(f"Employee record for {name} created successfully.")
                     print(f"Employee record for {name} created successfully.")
    else:
        employee_records = []
        employee_records.append(employee_data)
    
    with open('20_employee_records.json', 'w') as file:
            json.dump(employee_records, file, indent=4) 
    
    return {
         "status": "success",
         "message": "Employee record created",
         "record": employee_data
         }
def main():
    logger.info("\n...inside the main process...") # this logs an informational message indicating that the agent creation process is starting
    try:
        llm = create_gemini_llm()
    except Exception as e:
        logger.error(f"Error creating Gemini LLM instance: {e}")
        print(f"Error creating Gemini LLM instance: {e}")
        raise e
    logger.info("Gemini LLM instance created successfully.") # this logs an informational message indicating that the Gemini LLM instance has been created successfully
    logger.info("Creating agent with tools...") 
    agent = create_langchain_agent(model=llm, tools=[create_or_update_employee])
    return agent
if __name__ == "__main__":
    agent = main()
    logger.info("\n...invoking agent...") # this logs an informational message indicating that the agent is being invoked
    print("\n...invoking agent...")
    question = input("Enter your question for the agent: ")
    answer = agent.invoke(
         {"messages": [{"role": "user", "content": question}]}
    )
    final_answer = answer["messages"][-1].content
    print(f"Agent response: {final_answer}")

    print("\n\n\nAgent response:", answer)
