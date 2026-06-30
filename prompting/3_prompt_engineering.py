# This is for prompt Engineering
# in Zero Shot Prompting, we will give the model a prompt without any examples and ask it to generate a response.
# in Few Shot Prompting, we will give the model a prompt with a few examples and ask it to generate a response.
# in Chain of Thought Prompting, we will give the model a prompt with a few examples and ask it to generate a response while also explaining its reasoning process. 
# we will have one function for setting up imports and Gemini API client, and then we will have three separate functions for each prompting technique, and finally we will have a main function to call these functions and demonstrate their functionality.
# we will work along with Zero Shot Prompting, Few Shot Prompting, Chain of Thought Prompting, and finally we will create a custom prompt template using langchain's PromptTemplate class and use it to generate a response from the Gemini API.

""" 
The program starts with setting up the Gemini API client using the genai library and 
then defines a function to generate text from a given prompt. 
The function takes a string prompt as input, sends it to the Gemini API using the client, 
and prints the generated response text. Finally, it calls the function with a sample input 
prompt to demonstrate its functionality.
"""
from http import client # this is for making HTTP requests to the Gemini API
# this is necessary for setting up the Gemini API client and making requests to it. 
# We will use the genai library to interact with the Gemini API, 
# which is a Python client library for the Gemini API. We will also use the langchain library 
# to create custom prompt templates and generate responses from the Gemini API.

import os
from google import genai
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate

load_dotenv()

client = None

def setup_gemini_client():
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    # Global client variable to be used in all functions
    global client
    client=genai.Client(api_key=GEMINI_API_KEY)
    # Global client variable to be used in all functions

def generate_text(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


def zero_shot_prompting():
    #lets expand this for Tone, topic and length of the response
    print("\n\nWelcome to the Gemini LLM zero shot prompting demo!\n\n")

    topic = input("Please enter a topic for the prompt: ")
    tone = input("Please enter a tone for the response (e.g., formal, casual, humorous): ")
    length = input("Please enter the desired length of the response (e.g., short, medium, long): ")

    input_prompt = f"Write a {length} story about {topic} in a {tone} tone."
    response = generate_text(input_prompt)
    print(response)

def few_shot_prompting():
    print("\n\n Welcome to the Gemini LLM few shot prompting demo!\n\n")
    
    topic = input("Please enter a topic for the prompt: ")
    tone = input("Please enter a tone for the response (e.g., formal, casual, humorous): ")
    length = input("Please enter the desired length of the response (e.g., short, medium, long): ")

    example_template = """You are writing in the style of BBC News.
Examples:
1. The UK government has announced a new climate plan targeting net zero by 2050.
2. The US economy shows recovery signs after COVID-19 with falling unemployment.

Now write a similar report.

Topic: {topic}
Tone: {tone}
Length: {length}

Explanation:
"""

    final_prompt = PromptTemplate(
        input_variables=["topic", "tone", "length"],
        template=example_template
    ).format(topic=topic, tone=tone, length=length)

    print(f"Final prompt to be sent to Gemini API: {final_prompt}") 
    response = generate_text(final_prompt)
    print(response)


def chain_of_thought_prompting():
    print("Welcome to the Gemini LLM chain of thought prompting demo!\n\n")

    question = input("Enter a math word problem or reasoning question: ")

    cot_template = """You are a helpful assistant that solves problems by thinking step-by-step.

Question: {question}

Let's think through the problem step-by-step:
1.
"""

    prompt = PromptTemplate(
        input_variables=["question"],
        template=cot_template
    ).format(question=question)

    
    print(f"Sending prompt to Gemini:\n{prompt}\n")

    response = generate_text(prompt)

    print("Model's step-by-step reasoning and answer:")
    print(response)

#now main function to call the above functions and demonstrate their functionality

def main():
    setup_gemini_client()
    zero_shot_prompting()
    few_shot_prompting()
    chain_of_thought_prompting()
    

if __name__ == "__main__":
    main()

