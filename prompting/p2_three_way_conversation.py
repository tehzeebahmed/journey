"""
Three-way LLM conversation:
- Sarah   (Groq)    : Python student, asks questions
- Pasha   (Mistral) : Python tutor, answers
- Critic  (Gemini)  : Argumentative bot, criticizes both
"""
import os
from tee_logger import start_tee, stop_tee
import config
from openai import OpenAI


tee = start_tee(__file__)
gemini_client = OpenAI(api_key = os.getenv("GEMINI_API_KEY"), base_url = os.getenv("GEMINI_BASE_URL"))
mistral_client = OpenAI(api_key = os.getenv("MISTRAL_API_KEY"), base_url = os.getenv("MISTRAL_BASE_URL"))
groq_client = OpenAI(api_key = os.getenv("GROQ_API_KEY"), base_url = os.getenv("GROQ_BASE_URL"))


SARAH_SYSTEM = " you are Sarah a python student who started learning python in May 2026, ask one genuine short question about the topic conversation is going on so far"
PASHA_SYSTEM = " You are a python tutor with deep understanding of application of python concepts into business problems and clarifys things to Sarah in very short with just 2 line"
CRITIC_SYSTEM = " You are ctic and very argumentive, reads the conversation and criticise both and list down 5 bullets based on disagreemnent on what just said - short and blunt"

print('-' * 100)
Initial_question = input("\n\n What topic we want to discuss today? ")
num_turns = 5

#-------- API calls 

def call_mistral(messages):
    response = mistral_client.chat.completions.create(model = os.getenv("MISTRAL_MODEL_NAME"),
                                                      messages = messages,
                                                      temperature = 0.7, 
                                                      max_tokens = 502)
    return response.choices[0].message.content

def call_grok(messages):
    response = groq_client.chat.completions.create(model = os.getenv("GROQ_MODEL_NAME"),
                                                   messages = messages,
                                                   temperature = 0.7,
                                                   max_tokens = 502)
    return response.choices[0].message.content

def call_gemini(messages):
    response = gemini_client.chat.completions.create(model = os.getenv("GEMINI_MODEL_NAME"),
                                                     messages = messages,
                                                     temperature = 0.7,
                                                     max_tokens = 502)
    return response.choices[0].message.content

#____________chat history manager
class chatManager:
    def __init__(self):
        self.history = []
        # stores all turns as strings
    
    def add_conversation(self, sender, text):
        self.history.append(f" {sender}: {text}")    
    
    def add(self, sender, text):
        self.history.append(f"{sender}: {text}")            # fixed: was returning None
 
    def get_context(self):
        "Returns all history as one string"
        return "\n".join(self.history)
        
    def build_message(self, system_prompt):
        """
        Builds the messages list each model needs.
        System prompt sets the role, then the full conversation
        history is passed as the user message so the model has context.
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Here is the conversation so far:\n{self.get_context()}\n\nNow respond in your role."}
        ]

chat = chatManager()

# __________ main chat loop 
def run_llm_debate(turns: int = num_turns):
    # seed the opening message outside of loop
    chat.add_conversation("topic", Initial_question)

    for turn in range(turns):
        print('-' * 100)
        print(f" turn {turn +1} of {turns}")
        print('-' * 100)


        # --------Sarah (groq asks a question)
        sarah_message = chat.build_message(SARAH_SYSTEM)
        sarah_reply = call_grok(sarah_message)
        chat.add_conversation("Sarah", sarah_reply)
        print(f" Sarah reply -  {sarah_reply}")
        print('-' * 100)
        
        # --------- Tutor Pasha respond (Mistral answer)
        tutor_message = chat.build_message(PASHA_SYSTEM)
        tutor_reply = call_mistral(tutor_message)
        chat.add_conversation("Pasha", tutor_reply)
        print(f" Tutor Reply : {tutor_reply}")
        print('-' * 100)

        #----------- chatbot assistant reply (Gemini Critisize both)
        critic_message = chat.build_message(CRITIC_SYSTEM)
        #print(critic_message)   # ← add this temporarily
        critic_reply = call_gemini(critic_message)
        chat.add_conversation("Critic", critic_reply)
        print(f" Critic reply : {critic_reply}")
        print('-' * 100)
    print('-' * 100)
    print("-------- conversation Ended -------")
    print('*' * 100)

print(f"{'-'*60}")
print ("llm Debate Ends")

def main():
    run_llm_debate()
    stop_tee(tee)

if __name__ == '__main__':
    main()    





