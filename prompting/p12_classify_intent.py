"""
this script is for classifying the intent of the agent
"""
import config
from openai import OpenAI
import os
from datetime import datetime
from tee_logger import start_tee, stop_tee

client = OpenAI(api_key = os.getenv("GEMINI_API_KEY"), base_url = os.getenv("GEMINI_BASE_URL"))

def classify_intent(user_input: str) -> str:
    """
    sends user message to LLM and respond to user query with 
    accoun_brief/payment_history/log_promise/escalate/show_queue/unknown
    """
    PROMPT = f"""
you are an intent classifier for banking collection copilot.
classify the user's messages into exactly from one of these intents:
- account_brief : agent wants summary of account
- payment_history: agent wants payment timelines
- log_promise: customer made a payment promise
- escalate : agant wants to flag the account for legal
- show_queue: agents want to see their work queue
- unknown: None of the above

reply with only intent label, no other information/text
User Message: "{user_input}" 
Intent: """

    messages = [{"role": "system", "content": PROMPT}]
    # print(f"User Input: {user_input} \nIntent: {chat(messages)}")
    # response = client.chat.completions.create(model = os.getenv("GEMINI_MODEL_NAME"), messages = PROMPT, temperature=0.7)

    response = client.chat.completions.create(model = os.getenv("GEMINI_MODEL_NAME"),
                                            messages = [
                                               {"role": "system", "content": PROMPT},
                                               {"role": "user", "content": user_input}
                                            ], temperature = 0.7)
    print(f"\nUser query: {user_input} \nIntent: {response.choices[0].message.content}")


def main():
        tee_stream = start_tee(__file__)
        now = datetime.now()
        print('=' * 70)
        print(f"Copilot started @{now}")
        print('=' * 70)
        customer_response = input("\n Enter customer response please : ")
        print(customer_response)
        extract_promise = classify_intent(customer_response)
        # print(extract_promise)
        now = datetime.now()
        print('=' * 70)
        print(f"Copilot quit @{now}")
        print('=' * 70)
        stop_tee(tee_stream)

if __name__ == "__main__":
    main()
