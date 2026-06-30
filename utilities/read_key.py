#!/Users/mustafapasha/LangChain/projects/llm_engineering/.venv/bin/python3

# Load environment variables in a file called .env
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
#load_dotenv()


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

api_key = os.getenv("MISTRAL_API_KEY")

# Check the key

if not api_key:
    print("❌ No API key was found - please check your .env file placement!")
elif api_key.strip() != api_key:
    print("❌ An API key was found, but it has space or tab characters at the start or end - please remove them!")
else:
    print("✅ API key found and looks good!")
    # Optional: Print the first few characters to be 100% sure it's reading the right value
    print(f"Key starts with: {api_key[:5]}...") 

