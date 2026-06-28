import os
from dotenv import load_dotenv
from pathlib import Path
import sys
import requests
from google import genai
from google.genai import types


# sys.executable gives the exact path to the python program currently running 
# (e.g., /Users/.../llm_engineering/.venv/bin/python3)
python_bin_dir = Path(sys.executable).parent
print(python_bin_dir)

# Point directly to the .env file sitting in that exact bin/ folder
env_path = python_bin_dir / '.env'
print(env_path)

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Auto-located .env via active Python environment: {env_path}")
else:
    print(f"❌ Could not find .env in your active environment binary folder: {python_bin_dir}")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("api key not found check the env file")
else:
    print("api key found - start resume go ahead")

# FIX: Ensure there are no trailing characters attached to ".com"
endpoint_url = f"https://generativelanguage.googleapis.com"
print()

# Set HTTP headers for the request including Bearer token for authorization
header = {
    "authorization": f"Bearer {api_key}",
    "Content-type":  "application/json"
}
#define the data payload
data = {
    "model": "gemini-2.5-flash",
    "prompt": "You are a helpful python teacher who explain things easy super easy to understand for your students",
    "temperature": "0.7"
}

#make a post request for Gemini API
response = requests.post(endpoint_url, headers=header, json=data)

# 6. Check status and safely extract the text response
print("HTTP Status Code:", response.status_code)

if response.status_code == 200:
    response_json = response.json()
    try:
        # Safely parse Google's nested response structure
        generated_text = response_json["candidates"][0]["content"]["parts"][0][
            "text"
        ]
        print("\nGenerated Text:\n", generated_text)
    except (KeyError, IndexError):
        print("Failed to parse the expected fields. Raw response:", response_json)
else:
    print("Error Details:", response.text)
