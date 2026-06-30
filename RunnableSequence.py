# This script demonstrates creating a runnable sequence for data enrichment 
# and AI text generation using LangChain and Google's Gemini model.

# Import necessary libraries
from langchain_core import RunnableSequence, RunnableLambda  # LangChain's core workflow tools
from google import googleGenerativeAi, Client  # Google's Gemini client for AI text generation
from dotenv import load_dotenv  # Utility to load environment variables from a .env file
import os  # To access environment variables

# Load environment variables from the .env file
load_dotenv()
# Extract API key and model name from environment variables
API_KEY = os.getenv("API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

# Check if API key is loaded; if not, raise an error to alert the user immediately
if not API_KEY:
    raise ValueError("API key not found. Please set your API_KEY in the .env file.")

# Configure the Gemini client with the API key
client = Client(api_key=API_KEY)

# Create a model instance specifying which Gemini model to use
model = client.get_model(GEMINI_MODEL)

# Function to enrich product data by looking up additional details
def enrich_product_data(product_name):
    # Simulated product database as a dictionary
    product_catalog = {
        "Smartdesk": {"category": "Furniture", "price": 299},
        "EcoBottle": {"category": "Kitchen", "price": 19},
        "Noiseblock Pro": {"category": "Electronics", "price": 99},
    }
    # Look up product details; if not found, use default values
    details = product_catalog.get(product_name, {"category": "Misc", "price": 0})

    # Return a dictionary with enriched product data
    return {
        "name": product_name,
        "category": details["category"],
        "price": details["price"],
    }

# Function to build a prompt string for Gemini using enriched product data
def build_prompt(enriched_data):
    # Create a descriptive prompt including product name, category, and price
    prompt = (
        f"Write a marketing description for a product named {enriched_data['name']}, "
        f"which belongs to the {enriched_data['category']} category and costs ${enriched_data['price']}."
    )
    return prompt

# Function to call the Gemini model with the prompt and return generated text
def llm_call(prompt_text):
    # Send the prompt to the Gemini model and get the response
    response = model.generate_text(prompt=prompt_text)
    # Return only the generated text part of the response
    return response.text

# Wrap each function in RunnableLambda to make them modular workflow steps
enrich_step = RunnableLambda(enrich_product_data)
prompt_step = RunnableLambda(build_prompt)
llm_step = RunnableLambda(llm_call)

# Assemble the steps into a runnable sequence using the pipe operator
pipeline = enrich_step | prompt_step | llm_step

# Main execution block
if __name__ == "__main__":
    print("=== Product Marketing Description Generator ===")

    # Prompt user to enter a product name
    product_name = input("Enter a product name (e.g., Smartdesk, EcoBottle, Noiseblock Pro): ")

    # Run the entire pipeline with the product name as input
    marketing_description = pipeline.invoke(product_name)
    # Print the generated marketing description

    print("\nGenerated Marketing Description:")
    print(marketing_description)


"""
### Explanation of Key Components:

- **load_dotenv()**: Loads environment variables from a `.env` file so sensitive info like API keys are not hardcoded.
- **os.getenv()**: Retrieves environment variables by name.
- **RunnableLambda**: Wraps a function to make it a modular, reusable step in a LangChain workflow.
- **RunnableSequence (using pipe `|`)**: Chains multiple runnable steps into a linear pipeline where output of one step feeds into the next.
- **model.generate_text()**: Calls the Gemini AI model to generate text based on the prompt.

### How the script works:

1. It loads API credentials securely.
2. Defines a function to enrich product data with category and price.
3. Builds a prompt string for the AI model.
4. Sends the prompt to Gemini to generate a marketing description.
5. Combines these steps into a clean, reusable pipeline.
6. Takes user input and outputs a polished marketing description with a single function call.

This modular design makes it easy to test, maintain, and extend each part independently while keeping the overall workflow simple and clear.

If you'd like, I can help explain any specific part or function in more detail! Is there any other concept from this script you'd like me to clarify?
"""
