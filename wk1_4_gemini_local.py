from google import genai
import config

print("Connecting to Gemini...")

client = genai.Client()
try:
    if client:
        print(" Key found")
except:
    print("none finding")

print("Client initialized locally.")

# The script stops here and waits for your input in the terminal!
user_question = input("\n👉 Type your question here and press ENTER: ")

response = client.models.generate_content(model='gemini-2.5-flash', contents=user_question)

print (response.text)
