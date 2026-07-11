"""
code analyzer
for a given python file it analyzes for standrads, loopholes and errors in the code and suggests alternatives"""

import os
import config
from llm_router import chat
from tee_logger import start_tee, stop_tee
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url=os.getenv("GEMINI_BASE_URL"))

# if client: print('clint') else:  print("nono was loaded")

SYSTEM_PROMPT = "you are a python expert with 100 hard core comlex projects implementation. you analyze the python code for syntax correctness, logical safety, style compliance, execution performance, and structural architecture and you provide examples for the correction. you also provide the Flow of the script step1 -> step2"

def codeanalyze(filename: str):
    if not os.path.exists(filename):
        raise FileNotFoundError(f" File not found - {filename}")
    with open(filename, "r") as file:
        file_content = file.read()
        print(f"Analyzing file  - {filename} ........")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze this file conent and provide your inputs - {file_content}"}
    ]
    response = client.chat.completions.create(model=os.getenv("GEMINI_MODEL_NAME"),
                                              messages=messages, temperature=0.7
    )
    
    # response = chat(messages)
    return response.choices[0].message.content
    # return "......"

def main():
    tee = start_tee(__file__)
    user_file_name = input("provide the file name :")
    result = codeanalyze(user_file_name)
    print(result)
    stop_tee(tee)

if __name__ == '__main__':
    main()    