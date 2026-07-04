import os
from openai import OpenAI
from dotenv import load_dotenv
from google import genai
from google.genai import Client
import config
from  llm_router import chat
from tee_logger import start_tee, stop_tee

tee= start_tee(__file__)
messages=[
        {"role": "system", "content": 'You are a 20 yars experienced in AI teaching to Kids'},
        {"role": "user", "content": input(" write your technical question here :")}
    ]

reply = chat(messages)
print(reply)

stop_tee(tee)
