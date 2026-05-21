"""
This is for Project Personal Bio Generator, which demonstrates how to create a personal bio generator using Google Gemini LLM and LangChain.
The project includes:
- Setting up environment and configuration- Creating prompt templates for different tones/styles- Building a processing chain using LCEL
- Handling input validation and error management- Providing example usage and testing   
"""

# Project 1: Personal Bio Generator

## Description
# Generate professional bios in multiple styles (formal, casual, creative) 
# based on user information.

## Concepts Demonstrated
# - PromptTemplate with variables
# - Multiple prompt variations
# - LCEL composition with pipe operator
# - Output parsing


import os  
# Provides functions to interact with the operating system, e.g., environment variables
import logging  
# Enables logging for tracking events and debugging
from typing import Dict  
# Imports Dict type hint for specifying dictionary types in function signatures
from dotenv import load_dotenv  
# Loads environment variables from a .env file into the system environment
from langchain_google_genai import ChatGoogleGenerativeAI  
# Wrapper to interact with Google Gemini LLM
from langchain_core.prompts import PromptTemplate  
# Used to create structured prompt templates for LLM input
from langchain_core.output_parsers import StrOutputParser  
# Parses LLM output into string format

# Setup
load_dotenv()  
# Load environment variables from .env file into the environment
logging.basicConfig(level=logging.INFO)  
# Configure logging to show INFO level and above messages
logger = logging.getLogger(__name__)  
# Create a logger named after the current module

print("\n" + "="*70)  
# Print a newline and a separator line of 70 equal signs for console output clarity
print(logger.name.center(70))  
# Print the logger's name centered within 70 characters as a header


class BioGenerator:
    def __init__(self):
        """Initialize the bio generator."""
        # Initialize the Gemini LLM with specified model, temperature, and timeout
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Specify Gemini model version
            temperature=0.7,  
            # Controls randomness of output; 0.7 is moderately creative
            timeout=60  # Maximum wait time in seconds for a response
        )
        logger.info(" BioGenerator initialized")  # Log info message indicating initialization

    # LLM bootstrap : Gemini via google-generativeai, wrapped for LCEL

    # Retrieve Gemini API key from environment variables
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        # Raise error if API key is not set, instructing user to set it in environment
        raise RuntimeError("GEMINI_API_KEY is not set, please set it in the environment.")
  
    # Initialize Gemini model (langchain wrapper)
    # This comment indicates that the Gemini LLM instance is already initialized in __init__

    def generate(self, name: str, position: str, years: int, skills: str) -> Dict[str, str]:
        """Generate bios in multiple styles."""
        # Method to generate different styles of personal bios based on input parameters
        # Parameters:
        #   name (str): Person's name
        #   position (str): Job title or position
        #   years (int): Years of experience
        #   skills (str): Skills description
        # Returns:
        #   Dict[str, str]: Dictionary with keys 'formal', 'casual', 'creative' and corresponding bio strings

        # Input validation to ensure required fields are provided
        if not all([name, position, skills]):
            # Raise error if any of the required fields are missing or empty
            raise ValueError("Name, position, and skills are required")

        # Prepare input data dictionary with all inputs converted to strings as needed
        input_data = {
            "name": name,
            "position": position,
            "years": str(years),  # Convert years to string for prompt formatting
            "skills": skills
        }

        # Formal bio prompt template creation using LangChain's PromptTemplate
        formal_prompt = PromptTemplate.from_template(
            "Create a formal professional bio:\n"
            "Name: {name}\n"
            "Position: {position}\n"
            "Years: {years}\n"
            "Skills: {skills}"
        )
        # Chain the prompt template with the LLM and output parser using the pipe operator
        formal_chain = formal_prompt | self.llm | StrOutputParser()
        # Invoke the chain with input_data to generate the formal bio string
        formal_bio = formal_chain.invoke(input_data)

        # Casual bio prompt template for a friendly, informal style
        casual_prompt = PromptTemplate.from_template(
            "Create a casual, friendly bio:\n"
            "Name: {name}\n"
            "Position: {position}\n"
            "Years: {years}\n"
            "Skills: {skills}"
        )
        # Chain prompt, LLM, and parser for casual bio generation
        casual_chain = casual_prompt | self.llm | StrOutputParser()
        # Generate casual bio by invoking the chain with input data
        casual_bio = casual_chain.invoke(input_data)

        # Creative bio prompt template with emoji and creative style
        creative_prompt = PromptTemplate.from_template(
            "Create a creative, emoji-filled bio:\n"
            "Name: {name}\n"
            "Position: {position}\n"
            "Years: {years}\n"
            "Skills: {skills}"
        )
        # Chain prompt, LLM, and parser for creative bio generation
        creative_chain = creative_prompt | self.llm | StrOutputParser()
        # Generate creative bio by invoking the chain with input data
        creative_bio = creative_chain.invoke(input_data)

        # Return a dictionary containing all three generated bios
        return {
            "formal": formal_bio,
            "casual": casual_bio,
            "creative": creative_bio
        }

def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("PERSONAL BIO GENERATOR".center(70))
    print("="*70 + "\n")
    
    try:
        generator = BioGenerator()
        
        # Get user input
        print("Enter your information:")
        name = input("Full Name: ").strip()
        position = input("Job Position: ").strip()
        years = int(input("Years of Experience: ").strip())
        skills = input("Skills (comma-separated): ").strip()
        
        # Generate
        print("\n Generating bios...")
        bios = generator.generate(name, position, years, skills)
        
        # Display
        print("\n" + "="*70)
        print(" FORMAL BIO:")
        print(bios['formal'])
        print("\n CASUAL BIO:")
        print(bios['casual'])
        print("\n CREATIVE BIO:")
        print(bios['creative'])
        print("="*70 + "\n")


        # add to the file for testing
        with open("generated_bios.txt", "w") as f:
            
            f.write("FORMAL BIO:\n\n")
            f.write(bios['formal'] + "\n\n")
            
            f.write("CASUAL BIO:\n\n")
            f.write(bios['casual'] + "\n\n")
            
            f.write("CREATIVE BIO:\n\n")
            f.write(bios['creative'] + "\n")
        
    except Exception as e:
        print(f" Error: {e}")
        return 1
    # the program catches the error and shows a friendly message instead of crashing. This makes the program robust and user-friendly.

    return 0

if __name__ == "__main__":
    exit(main())

