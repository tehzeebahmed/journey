"""
This script is used to get the json data from the llm response
"""

from tee_logger import start_tee, stop_tee
from llm_router import chat
from datetime import datetime

def agent_extract_promise(user_message: str):
    """Extract promise amount and date date from the user message and 
    return {'promise_amout:' float, 'date:' str}"""
    prompt = f"""
    Extract the payment promise details from this message
    return on valid two fields in strict json format and no other value
    "amount": the promised payment amount as number
    "date:" the promised date in DD-MON-YYYY format
    if today is {datetime.date} and agent says friday you calculate the actual date from today for next promise date
    if no date or amount mentioned then return 'No updates from customer'
    
    message:{user_message}
    json:"""
    message = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_message}
    ]
    print('-' * 70)
    llm_output = chat(message)
    start_index = llm_output.find("{")
    end_index = llm_output.find("}") + 1
    print(llm_output[start_index:end_index])
    print('-' * 70)

def main():
        tee_stream = start_tee(__file__)
        now = datetime.now()
        print('=' * 70)
        print(f"Copilot started @{now}")
        print('=' * 70)
        customer_response = input("\n Enter customer response please : ")
        print(customer_response)
        extract_promise = agent_extract_promise(customer_response)
        # print(extract_promise)
        now = datetime.now()
        print('=' * 70)
        print(f"Copilot quit @{now}")
        print('=' * 70)
        stop_tee(tee_stream)

if __name__ == "__main__":
    main()
