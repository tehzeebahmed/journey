"""
This is for chatting two llms
one being as the instrcutor of python with extensive hans-on experience of 24 yesrs (gemini)
and the other one as very inquisitive student (mistral)

"""
import os
import config
from openai import OpenAI
from tee_logger import start_tee, stop_tee
#from llm_router import chat

tee = start_tee(__file__)

gemini_client = OpenAI(api_key = os.getenv("GEMINI_API_KEY"), base_url = os.getenv("GEMINI_BASE_URL"))
mistral_client = OpenAI(api_key = os.getenv("MISTRAL_API_KEY"), base_url = os.getenv("MISTRAL_BASE_URL"))

gemini_system = " you are python instructor with 24 years of hard code hands-on expelrience you explain things in very nicer way even though the student makes simple mistake you are very calm and very polite and crack jokes as well"

mistral_system = " you are a student of llm and python and you are very inquisitive you tend to be very inquisitive and seek nuisance of everything and you think on applying the topic in python program for solving problems"

OPENING_MESSAGE = "What is the biggest mistake companies make when building a python loop?"

NUM_TURNS = 5

def call_mistral(messages):
        response = mistral_client.chat.completions.create(model = os.getenv("MISTRAL_MODEL_NAME"),
                messages = messages,
                temperature = 0.7,
                max_tokens = 1024
            )
        return response.choices[0].message.content

def call_gemini(messages):
        response = gemini_client.chat.completions.create(model = os.getenv("GEMINI_MODEL_NAME"),
                messages = messages,
                temperature = 0.7,
                max_tokens = 1024
            )
        return response.choices[0].message.content

def run_llm_debate(turns: int = NUM_TURNS):

    gemini_message = [{"role": "system", "content": gemini_system}]
    mistral_message = [{"role": "system", "content": mistral_system}]
    print(f"{'-'*60}")

    for turn in range(turns):
          
          current_input = OPENING_MESSAGE
          # mistral recieves Gemini message 
          mistral_message.append({"role": "user", "content": current_input})
          mistral_reply = call_mistral(mistral_message)
          mistral_message.append({"role": "assistant", "content": mistral_reply}
                                 )
          print(f"{'-'*60}")
          print(f"\nMISTRAL: {mistral_reply}")
          print(f"{'-'*60}")

          #Gemini receives Mistral answer 
          gemini_message.append({"role": "user", "content": mistral_reply})
          gemini_reply = call_gemini(gemini_message)
          gemini_message.append({"role": "assistant", "content": gemini_reply})
          print(f"{'-'*60}")
          print(f"\n Gemini: {gemini_reply}")
          print(f"{'-'*60}")

          current_input = gemini_reply


    print(f"{'-'*60}")
    print ("llm Debate Ends")

def main():
       run_llm_debate()
       stop_tee(tee)

if __name__ == '__main__':
       main()

