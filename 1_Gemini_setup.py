# Setting up Gemini env
# 1. Install the Gemini SDK
# You can install the Gemini SDK using pip:
# pip install gemini-sdk
# 2. Set up your API key
# You need to set up your API key to authenticate with the Gemini API. You can do this by setting the GEMINI_API_KEY environment variable:
# export GEMINI_API_KEY="your_api_key_here"
# 3. Use the Gemini SDK in your Python code
# Here is an example of how to use the Gemini SDK to generate text:
import os
from google import genai

# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
    )

# model = genai.client("gemini-2.5-flash")

input_prompt = input("Enter a prompt to generate text: ")
print(f"Input prompt: {input_prompt}")

def generate_text(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    print(response.text)
    return response.text

generate_text(input_prompt)