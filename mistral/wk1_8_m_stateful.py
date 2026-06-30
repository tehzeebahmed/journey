'''
chat completions with mistral ai, it works on the line of openai response.choices[0].message.content
not like google's Gemini on chat.create or chat.interactions.create
it creates also a Tee to write to terminal and to file generated/opened at runtime
'''
import sys
from pathlib import Path
from mistralai.client import Mistral
import config
from datetime import datetime

client= Mistral()

class Tee:
    """Duplicate stdout to both terminal and file."""
    def __init__(self, filename):
        self.terminal = sys.__stdout__
        self.file = open(filename, "a", encoding="utf-8", buffering=1)
    def write(self, message):
        self.terminal.write(message)
        self.file.write(message)
    def flush(self):
        self.terminal.flush()
        self.file.flush()

#get the currentfilename 
text_filename = Path(__file__).with_suffix(".txt")
#redirect all the print statements into this text_filename and 
# 2. Redirect sys.stdout to our custom dual-writer
sys.stdout = Tee(text_filename)

print(f" file generation done ...{text_filename}")

messages = [
    {"role": "system", "content": "You are an assistant AI"}
]
print(" \n first role user added ...")
#first Interaction
messages.append(
    {"role": "user",
     "content": "My name is Tehzeeb Pasha and lives in Moradabad doing WFH for Novo"}
)

response1 = client.chat.complete(
    model="mistral-large-latest",
    messages=messages
)
reply1 = response1.choices[0].message.content
print(f"\n the first response is {reply1}")

messages.append(
    {"role":"assistant",
     "content": reply1}
)

#Second Interaction - testing out menmory
messages.append(
    {"role":"user", "content": input("write your question here - ")}
    )

response2 = client.chat.complete(
    model= "mistral-large-latest",
    messages=messages
)
reply2=response2.choices[0].message.content
print(f" \n the Second response from Memory is {reply2}")
print(
    f"\n\n---------------------End of execution - "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}---------------------"
)

if isinstance(sys.stdout, Tee):
    tee = sys.stdout
    sys.stdout = sys.__stdout__   # restore terminal first
    tee.file.close()   
