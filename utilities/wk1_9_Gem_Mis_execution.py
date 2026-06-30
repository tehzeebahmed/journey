'''
this is for a simple task and to be used mistral and gemini
multi LLM executions plus a config file for writing to terminal and file

'''

import sys
from datetime import datetime
from litellm import completion
from tee_logger import start_tee, stop_tee
from google import genai
from mistralai.client import Mistral
import config

tee = start_tee(__file__)

GEMINI_model = "gemini/gemini-2.5-flash"
MISTRAL_model= "mistral/mistral-large-latest"
gclient= genai.client
mclient= Mistral()

def ruun_chat_session (model_name):
    print(f" --- starting chat session with - {model_name}")
    messages = [
        {"role": "system", "content": " you are an helpful AI assistant"}
    ]

    user_input = input("1. Wrire your question here -  ")

    messages.append({"role": "user", "content": user_input})
    print(f"\n\n 1. user Input is {user_input}")

    response1 = completion(
        model=model_name,
        messages=messages
    )

    reply1 = response1.choices[0].message.content
    print(f"\n\n 2. assistant reply is -  {reply1}")

    messages.append({"role": "assistant", "content":reply1})

    #Second Interaction
    user_input2 = input("\n\n3. write your next input here - ")
    print(f" Second user input is - {user_input2}")

    messages.append({
        "role": "user", "content": user_input2
    })

    response2 = completion(model=model_name, messages=messages)
    reply2 = response2.choices[0].message.content
    messages.append(
        {"role": "assistant", "content": {reply2}}
    )
    print(f" \n\n *-*-4. Reply from AI on second Questions is {reply2}")

ruun_chat_session(GEMINI_model)   
ruun_chat_session(MISTRAL_model)

print(
    f"\n\n---------------------End of execution - "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}---------------------"
)

stop_tee(tee)