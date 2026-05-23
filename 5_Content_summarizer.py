#Content summarizer

"""


# **Description**: This project focuses on creating a versatile text summarizer that can condense any given text into three different lengths: short (50 words), medium (100 words), and long (200 words). The summarizer will preserve key information while providing a clear and concise summary. Additionally, 
# it will calculate the compression ratio to show how much the original text has been condensed.
# Summarize any given text in different lengths (short, medium, long).

## Inputs**:
# text: str (any length)
# summary_length: str (choices: "short"=50 words, "medium"=100 words, "long"=200 words)

## Features**:
# Summarize in 3 different lengths
# Show compression ratio (original vs summary)
# Multiple summaries for comparison
# Preserve key information

## Example Output**:

# Original (500 words) → Short Summary (50 words): 
" The article discusses AI's impact on healthcare, highlighting diagnostic accuracy, 
treatment personalization, and operational efficiency improvements."

# Compression Ratio: 90%


##**Implementation Hints**:

# Use length as a parameter in prompt
prompt = ChatPromptTemplate.from_template(
    "Summarize this text in exactly {word_count} words:\n{text}"
)

# Build chain and invoke with different word counts

# Evaluation Criteria**:
# [ ] Summaries actually meet word count constraints
# [ ] Key information preserved in summaries
# [ ] Compression ratio calculated correctly
# [ ] Works with various text lengths
# [ ] Clean output formatting

"""
from itertools import chain
from unittest import result


import os
from langchain_google_genai  import GoogleGenerativeAI, ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, ChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv  
# Loads environment variables from a .env file into the system environment
import logging  
# Enables logging for tracking events and debugging
from typing import Dict  
# Imports Dict type hint for specifying dictionary types in function signatures 

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

# Retrieve Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
        # Raise error if API key is not set, instructing user to set it in environment
        raise RuntimeError("GEMINI_API_KEY is not set, please set it in the environment.")


# Initialize the Gemini LLM instance
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=GEMINI_API_KEY)

# This module implements a content summarizer that can condense any given text into three different lengths: short (50 words), medium (100 words), and long (200 words). The summarizer preserves key information while providing clear and concise summaries. Additionally, it calculates the compression ratio to show how much the original text has been condensed.
# The summarizer is built using the Gemini LLM via the google-generativeai wrapper, and it utilizes structured prompt templates to ensure that the summaries meet the specified word count constraints while preserving key information.

def summarize_content(text: str, summary_length: str) -> Dict[str, str]:
    """
    Summarize the given text into specified lengths and calculate compression ratio.

    Args:
        text (str): The original text to be summarized.
        summary_length (str): The desired summary length ("short", "medium", "long").

    Returns:
        Dict[str, str]: A dictionary containing the original text, summary, and compression ratio.
    """
    # Define word count based on summary length
    word_counts = {
        "short": 50,
        "medium": 100,
        "long": 200
    }
        
    if summary_length not in word_counts:
        raise ValueError("Invalid summary length. Choose from 'short', 'medium', or 'long'.")

    word_count = word_counts[summary_length]
    
    # Create prompt template for summarization
    prompt = ChatPromptTemplate.from_template(
        "\n\nSummarize this text in exactly {word_count} words:\n{text}"
    )
    
    chain = prompt | llm | StrOutputParser()
    summary = chain.invoke({"word_count": word_count, "text": text})

    # Generate summary using Gemini LLM
    summary = llm.invoke(prompt.format(word_count=word_count, text=text))

    # Calculate compression ratio
    original_word_count = len(text.split())
    compression_ratio = 20#(1 - len(summary) / original_word_count) * 100
    
    return {
        "original_text": text,
        "summary": summary,
        "compression_ratio": f"{compression_ratio:.2f}%"
    }

def main(text: str, summary_length: str):
    """\nMain function to execute the content summarizer with example input."""
    # Example usage
    original_text = text
    result = summarize_content(original_text, summary_length)
    print("\n\nOriginal Text:", result["original_text"])
    print("\n\nSummary:", result["summary"])
    print("\n\nCompression Ratio:", result["compression_ratio"])
    print(result["summary"])

if __name__ == "__main__":
    text_input = input("Enter the text to summarize: ")
    length_input = input("Enter the desired summary length (short/medium/long): ")
    print(f"\n\nReceived summary_length: '{length_input}'\n\n")
    main(text_input, length_input)

