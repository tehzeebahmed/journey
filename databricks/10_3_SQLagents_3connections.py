
#This python file is to connect three data points with three agents
#1. databricks data will be fetched by claude agent and then it will be stored in a variable,
#2. snowflake will be fetched by open AI agent and then it will be stored in a variable,
#3. local csv file will be fetched by Gemini agent and then it will be stored in a variable.

#It will use open AI, Gemini and claude API key for three differebnt agents


import os
import logging
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the GEMINI LLMs for each agent
gemini_agent = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7
)
#initialize the other agents (OpenAI and Claude) here with their respective API keys and configurations
claude_agent = ChatGoogleGenerativeAI(
    model="claude-1",
    temperature=0.7
)
openai_agent = ChatGoogleGenerativeAI(
    model="gpt-4",
    temperature=0.7
)

def fetch_databricks_data():
    # Use the claude_agent to fetch data from Databricks
    logger.info("Fetching data from Databricks using Claude agent...")
    databricks_query = "SELECT * FROM your_databricks_table LIMIT 10;"
    #log and check if connection is successful to claude agent
    logger.info("Connecting to Claude agent...")
    databricks_data = claude_agent.invoke(databricks_query).text.strip()
    if databricks_data:
        logger.info("Data fetched successfully from Databricks.")
    else:        
        logger.error("Failed to fetch data from Databricks.")
    return databricks_data

def fetch_snowflake_data():
    # Use the openai_agent to fetch data from Snowflake
    logger.info("Fetching data from Snowflake using OpenAI agent...")
    snowflake_query = "SELECT * FROM your_snowflake_table LIMIT 10;"
    logger.info("Connecting to OpenAI agent...")
    snowflake_data = openai_agent.invoke(snowflake_query).text.strip()
    if snowflake_data:
        logger.info("Data fetched successfully from Snowflake.")
    else:
        logger.error("Failed to fetch data from Snowflake.")
    return snowflake_data

def fetch_local_csv_data():
    # Use the gemini_agent to fetch data from the local CSV file
    logger.info("Fetching data from local CSV file using Gemini agent...")
    csv_data = gemini_agent.invoke("Read the contents of the local CSV file.").text.strip()
    if csv_data:
        logger.info("Data fetched successfully from local CSV file.")
    else:
        logger.error("Failed to fetch data from local CSV file.")
    return csv_data

def main():
    databricks_data = fetch_databricks_data()
    snowflake_data = fetch_snowflake_data()
    local_csv_data = fetch_local_csv_data()

    # Now you have the data from all three sources stored in variables
    logger.info("Data fetched successfully from all sources.")
    #open a csv file and write the data from all three sources into it
    with open("combined_data.csv", "w", encoding="utf-8") as csv_file:
        csv_file.write("Databricks Data:\n")
        csv_file.write(databricks_data + "\n\n")
        csv_file.write("Snowflake Data:\n")
        csv_file.write(snowflake_data + "\n\n")
        csv_file.write("Local CSV Data:\n")
        csv_file.write(local_csv_data + "\n\n")
        
    print("Databricks Data:\n", databricks_data)
    print("\nSnowflake Data:\n", snowflake_data)
    print("\nLocal CSV Data:\n", local_csv_data)    
if __name__ == "__main__":
    main()