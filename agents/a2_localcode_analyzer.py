"""This agent acts as a local assistant that can read, write, and analyze python code in a specific folder on your computer and list suggestions.

[ User Prompt ] ---> "Look at test.py and see if it has bugs."
       |
       v
[ LLM Reason ] ---> "I need to see the code inside test.py first. 
                     I will call the 'read_file' tool."
       |
       v
[ Python App ] ---> Intercepts tool call -> Runs local Python function 
                     `open('test.py').read()` -> Gets code text.
       |
       v
[ LLM Review ] ---> Receives code text -> Analyzes it -> Returns final response:
                     "I found a bug on line 4..."

"""
import os
from pathlib import Path
from tee_logger import start_tee, stop_tee
from llm_router import chat

tee = start_tee(__file__)

SYSTEM_PROMPT = """You are a senior Python code reviewer with 20 years of experience.
When given a Python file, you:
1. Summarize what the code does in 2-3 lines
2. List any bugs or errors found
3. Give 5 specific improvement suggestions
4. Rate the code quality out of 10
Be concise and direct."""

script_dir = Path(__file__).resolve().parent
project_root = script_dir

def checkfile() -> str:
    if project_root.exists() and project_root.is_dir():
        print(f" Current project directory is {project_root}")
        # get all the files of this directory
        files = os.listdir(project_root)
        # Returns all the file names
        return (f" Files listed in {project_root} :\n " + "\n".join(files))
    else:
        return "error - project directory not known"

def readfile(filename: str) -> str:
    """Lists files in directory, takes filename input, returns file contents."""
    #filename = input("\n\n name the pythion file here : ")
    target_file_name = project_root / filename
    print(checkfile())
    try:
        # open and read file 
        with open(target_file_name, "r", encoding = "utf-8") as file:
            print("file read operation")
            return file.read()
        
    except FileNotFoundError:
        return f"Error : the file {filename} dows not exists in this directory {project_root}"
    except Exception as e:
        return f" Error reading file : {str(e)}"

def llm_code_analyser(code: str, filename: str) -> str:
    messages = [
    {"role": "system", "content": " you are a experienced python code analyser and you do a thorough check on python code and list down bullet points of your suggestions"},
    {"role": "user", "content": f"Please review this Python file '{filename}':\n\n{code}"}
]
    print(f"\n\n {filename } review under process .....")
    reply =chat(messages)
    return reply

def main():
    filename = input(" what python file you want to analyse : ").strip()
    code = readfile(filename)
    if code.startswith("Error"):
        print(code)
    else:
        print(f"this file -  {filename} is completely read")
        review = llm_code_analyser(code, filename)
        
        print(f"\n{'=' * 60}")
        print(" CODE REVIEW REPORT")
        print(f"{'=' * 60}")
        print(review)
        print(f"{'=' * 60}")

        stop_tee(tee)

if __name__ == '__main__':
    main()    
    





