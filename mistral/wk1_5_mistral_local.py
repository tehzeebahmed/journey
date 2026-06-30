from mistralai.client import Mistral
import config

# 1. Initialize the client (reads MISTRAL_API_KEY automatically)
client = Mistral()

# 2. Get a response using a model like 'mistral-large-latest'
response = client.chat.complete(
    model="mistral-large-latest",
    messages=[
        {
            "role": "user",
            "content": "What are three fun facts about space?"
        }
    ]
)

# 3. Print the text response
print(response.choices[0].message.content)