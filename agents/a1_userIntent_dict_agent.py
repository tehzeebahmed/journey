"""
this pythion program is for checking the python knowledge
it creates a tool and respond to the user
"""

import os
import config
from openai import OpenAI
from tee_logger import start_tee, stop_tee

tee= start_tee(__file__)

GROQ_CLIENT = OpenAI(api_key = os.getenv("GROQ_API_KEY"), base_url = os.getenv("GROQ_BASE_URL"))

def my_agent(user_intent):
    #explain tools and system rules
    messages = [
        {"role": "system", "content": " you are Pasha python expert you give python code with each line commented with explaination with why "},
        {"role": "user", "content": user_intent}
    ]

    # now iterate through the Loop
    while True:
        response = GROQ_CLIENT.chat.completions.create(model = os.getenv("GROQ_MODEL_NAME"), messages = messages)
        llm_response = response.choices[0].message.content
        print(llm_response)

        #check if user wants to exit
        next_input = input(" \n What is next question you have :")
        if next_input.strip() == "quit":
            print(f"{'-' * 60}  - goodbye -  {'-' * 60} ")
            return llm_response
        
        # Otherwise, append the thought and simulate a tool output
        messages.append({"role": "assistant", "content": llm_response})
        messages.append({"role": "user", "content": user_intent})

def main():
    user_input = input("\n\n what is your question sir :")
    my_agent(user_input)        
    stop_tee(tee)

if __name__ == '__main__':
    main()    
