import os
from langchain_google_genai import chatgoogleGenerativeAi
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

file_handler = logging.FileHandler('agentic.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

def initiate_llm():
    llm = chatgoogleGenerativeAi(model="gemini-2.5 Flash", temperature=0)
    return llm

def main():
    try:
        logger.info("Starting the agentic application.")
        llm = initiate_llm()
        logger.info("LLM initialized successfully.")
        # Use the initialized LLM here
    except Exception as e:
        logger.error(f"An error occurred in the initializing ...Exiting ...: {e}")

if __name__ == "__main__":
    main()