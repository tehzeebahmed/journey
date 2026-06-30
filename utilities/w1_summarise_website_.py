# Define our system prompt - you can experiment with this later, changing the last sentence to 'Respond in markdown in Spanish."

import os
from langchain_mistralai import ChatMistralAI
from mistral_common.protocol.instruct.tool_calls import Tool, Function
from mistralai.client import Mistral
# Import the function from your local scraper.py file
from scraper import fetch_website_contents
from langchain_google_genai  import GoogleGenerativeAI, ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()
import sys
from pathlib import Path

system_prompt = """
You are a snarky assistant that analyzes the contents of a website,
and provides a short, snarky, humorous summary, ignoring text that might be navigation related.
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
"""

# Define our user prompt

user_prompt_prefix = """
Here are the contents of a website.
Provide a short summary in 100 words of this website in capital letters only.
If it includes news or announcements, then summarize these too with the heading what it is.

"""

python_bin_dir = Path(sys.executable).parent
print(python_bin_dir)

env_path = python_bin_dir / '.env'
print(env_path)

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f" Auto-located .env via active Python environment: {env_path}")
else:
    print(f" Could not find .env in your active environment binary folder: {python_bin_dir}")


api_key = os.getenv("MISTRAL_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print(" No API key was found - please check your .env file placement!")
elif api_key.strip() != api_key:
    print(" An API key was found, but it has space or tab characters at the start or end - please remove them!")
else:
    print("API key found and looks good!")
    # Optional: Print the first few characters to be 100% sure it's reading the right value
    print(f"Key starts with: {GEMINI_API_KEY[:5]}...") 

#llm = ChatMistralAI(model="mistral-large-latest", temperature=0)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)


def messages_for(website_content):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + website_content}
    ]


def summarize(url):
    website_contents = fetch_website_contents(url)
    formatted_message = messages_for(website_contents)
    retresponse = llm.invoke(formatted_message)
    return retresponse.content

def main():
    ed = ("https://edwarddonner.com")
    print(f"summarizing and scraping the url {ed}..\n")
    
    summary = summarize(ed)
    print(summary)

if __name__ == "__main__":
    main()
    
