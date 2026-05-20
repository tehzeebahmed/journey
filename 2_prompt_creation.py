# first prompt generation 
# based on Topic, Tone and Length of the response
# using ChatGoogleGenerativeAI from langchain

import os
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini LLM weppper
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", api_key=GEMINI_API_KEY
    )

#now the function for generating text using the Gemini API
def Single_prompt_demo():
    
    print("Welcome to the Gemini LLM prompt generation demo!")
    topic = input("Please enter a topic for the prompt: ")
    tone = input("Please enter a tone for the response (e.g., formal, casual, humorous): ")
    length = input("Please enter the desired length of the response (e.g., short, medium, long): ")
    
    #Template for the prompt
    prompt_template = PromptTemplate.from_template(
        "Generate a {length} response in a {tone} tone about the topic: {topic}"
    )

    #format the prompt with the user inputs
    prompt = prompt_template.format(
        topic=topic, tone=tone, length=length
        )
    
    #final_prompt = ChatPromptTemplate.from_messages([prompt])
    final_prompt = prompt.format(topic=topic, tone=tone, length=length)

    # print the final prompt to be sent to the Gemini API
    print(f"Final prompt to be sent to Gemini API: {final_prompt}") 

    print("\n inserting it to Gemini LLM wrapper to generate the response... \n")
    response = llm.invoke(final_prompt)

    # this will print the raw response from the Gemini API and the generated text response
    print(f"\n\n Generated response from Gemini API: {response}")

    # this will priont only the generated text response from the Gemini API
    print(response.text)


if __name__ == "__main__":
    Single_prompt_demo()


    
    #generate the response using the Gemini LLM wrapper


                       