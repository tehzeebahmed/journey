import os
from mistralai.client import Mistral

print("Mistral AI SDK imported successfully.")

def ask_mistral():
    # Initialize client using environment variable
    api_key = os.environ.get("MISTRAL_API_KEY")
    client = Mistral(api_key=api_key)
    
    # Prompt user for input
    user_question = input("Enter your question for the LLM: ")
    
    try:
        # Execute chat completion query
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "user",
                    "content": user_question
                }
            ]
        )
        
        # Parse the reply payload
        answer = response.choices[0].message.content
        print(f"\n[Mistral Response]:\n{answer}")
        
    except Exception as e:
        print(f"API Error encountered: {e}")

if __name__ == "__main__":
    ask_mistral()
