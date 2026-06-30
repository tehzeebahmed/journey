import os
import sys
from dotenv import load_dotenv
from google import genai
from pathlib import Path

python_bin_dir = Path(sys.executable).parent
env_path = python_bin_dir / '.env'
load_dotenv(dotenv_path=env_path, override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("api key panga boss")
else:
    print ("all good Okie")

client = genai.Client()
response = client.models.generate_content(   model="gemini-2.5-flash",
    contents="Tell me a fun fact",
)
print(response.text)