'''
this is for keeping the memory using Gemni and printing all our interactions
'''

from google import genai
import config
from google.genai import types

client = genai.Client()

chat = client.chats.create(
    model="gemini-2.5-flash",
    config = types.GenerateContentConfig(
        system_instruction="you are an assitant AI"
    )
)

response1 = chat.send_message(" Hi I am Pasha")
print(f" the Response is : {response1.text}")

response2 = chat.send_message(" Hi what is my name?")
print(f" second time response is : {response2.text}")

# Print the entire conversation transcript stored in memory
for message in chat.get_history():
    print(f"Role: {message.role} --- {message.parts[0].text}")
