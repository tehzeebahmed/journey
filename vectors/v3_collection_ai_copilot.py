import os
import json
import config
import sys
from pathlib import Path
from tee_logger import start_tee, stop_tee
from datetime import datetime, timedelta
from pydantic import BaseModel
from llm_router import chat
from openai import OpenAI
from google import genai
import chromadb
from mistralai.client import Mistral
from sentence_transformers import SentenceTransformer

from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

# client = OpenAI(api_key = os.getenv("GEMINI_API_KEY"), base_url = os.getenv("GEMINI_BASE_URL"))
# client = OpenAI(api_key = os.getenv("GEMINI_API_KEY"), base_url = os.getenv("GEMINI_BASE_URL"))

api_key = os.getenv("MISTRAL_API_KEY")
CURR_PATH = Path(__file__).parent
ACCOUNT_FILE_PATH = CURR_PATH.joinpath("v3_accounts.json") # account holder and details
CALLLOG_FILE_PATH = CURR_PATH.joinpath("v3_call_log.json") # call summary / per call
AGENT_FILE_PATH   = CURR_PATH.joinpath("v3_agent_performance_report.json")   # agent id, name, lotal tickets per months
POLICY_FILE_PATH = CURR_PATH.joinpath("v3_collections_policy.txt")
WHO_AM_I = "" #Agent whio is running this script - need this variable in call log update
db_path = "./local_vectordb"
COLLECTION_NAME = "escalationpolicy"
FREECOLLECTION_NAME = "freeescalationpolicy"
embedder = SentenceTransformer('all-MiniLM-L6-v2')
# embeddings = model.encode(POLICY_FILE_PATH)

def embed(texts: list[str]) -> list:
    return embedder.encode(texts).tolist()

class ConversationState(BaseModel):
    # ── Session ────────────────────────────────────────
    session_id:    str
    agent_id:      str
    agent_name:    str
    # ── Account details ────────────────────────────────
    account_id:    str
    customer_name: str
    phone:         str
    product_type:  str        # "personal_loan" / "home_loan" / "credit_card"
    # ── Financial position ─────────────────────────────
    overdue_amount:     float
    overdue_days:       int
    last_payment_date:  str
    last_payment_amount: float
    # ── Promise to pay ─────────────────────────────────
    promise_amount: float = 0.0
    promise_date:   str   = ""
    notes:          str   = ""
    # ── Risk classification ────────────────────────────
    risk_level: str = "normal"   # "normal" / "urgent" / "critical"
    # ── Escalation flags ───────────────────────────────
    escalate_to_rm:    bool = False
    escalate_to_legal: bool = False
    # ── Conversation memory (multi-turn) ───────────────
    messages: list[dict] = []    # full chat history
    # ── Outcome tracking ───────────────────────────────
    action_taken:  str = ""      # what copilot did this session
    notes:         str = ""      # agent's call notes
    log_date:      str = ""      # when this was logged
    # ── RM handoff ─────────────────────────────────────
    rm_summary:    str = ""      # auto-generated summary for RM

def initiate_chroma_client(path: str) ->chromadb.PersistentClient:
    """ initializes and returns chromadb persistantclient"""
    print(f"\nStep 1. Initializing chromadb client at : {path}")
    return chromadb.PersistentClient(path=path)

def chunks_by_section(text: str) -> list[str]:
    import re
    sections = re.split(r'\n\n(?=Section \d+)', text)
    return [s.strip() for s in sections if s.strip()]

# EMBEDDING_FUNCTION_GEMINI = customEmbedding_fn()
def build_knowledge_base(client: chromadb.Client, text_content: str)-> chromadb.Collection:
    """create collection and index """
    collection = client.get_or_create_collection(name = FREECOLLECTION_NAME, 
                                     metadata = {"hnsw:space": "cosine"} # use cosine similarity
                                    #  embedding_function = embedding_func
                                    )  # ChromaDB calls this automatically

    if collection.count() == 0:
        chunks = chunks_by_section(text_content)  # ← split into sections first
        print(f"[RAG] Indexing {len(chunks)} sections...")
        collection.add(
            ids        = [f"chunk_{i}" for i in range(len(chunks))],
            documents  = chunks,
            embeddings = embed(chunks)   # ← embed all at once
        )
        print(f"[RAG] {collection.count()} chunks indexed")
    else:
        print(f"[RAG] Collection already has {collection.count()} chunks")

    return collection

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
Intent: """
#  User Message: "{user_input}" 

    messages = [{"role": "system", "content": PROMPT},
                {"role": "user",   "content": user_input}  ]
    intent = chat(messages)
    print(f"User Input: {user_input} \nIntent: {intent}")
    return intent

    # response = client.chat.completions.create(model = os.getenv("GEMINI_MODEL_NAME"), messages = PROMPT, temperature=0.7)

    # response = client.chat.completions.create(model = os.getenv("GEMINI_MODEL_NAME"),
    #                                         messages = [
    #                                            {"role": "system", "content": PROMPT},
    #                                            {"role": "user", "content": user_input}
    #                                         ], temperature = 0.7)
    # print(f"\nUser query: {user_input} \nIntent: {response.choices[0].message.content}")

def agent_show_queue(state_list: list[ConversationState], who_agent: str)-> str:
    """It reads state and list down all the accounts sorted by overdue days"""
    current_state = ConversationState
    with open(CALLLOG_FILE_PATH, "r") as call_read_f:
        call_log = json.load(call_read_f)
        # print(len(call_log))
    with open(ACCOUNT_FILE_PATH, "r") as cacc_read_f:
            all_accounts_list = json.load(cacc_read_f)
    with open(AGENT_FILE_PATH, "r") as agent_file_read:
        agent_details = json.load(agent_file_read)
        for i in agent_details:
            if who_agent == i.get("agent_id"):
                agent_name = i.get("agent_name")
    # ----------------------------------
    # get all account ID for who_agent
    # ----------------------------------
    account_ids_for_agent = {
        log.get("account_id") for log in call_log if log.get("agent_id") == who_agent}
    # print(account_ids_for_agent)
    # ----------------------------------------------------
    # get all account ID for who_agent Lookup basically 
    # ----------------------------------------------------
    account_details_for_agent = [
        acc for acc in all_accounts_list if acc.get("account_id") in account_ids_for_agent]
    all_overdue_acc_sorted = sorted(account_details_for_agent, key=lambda s: s.get('overdue_days'), reverse=True)

    if not all_overdue_acc_sorted:
        print(f"\n There are no accounts to follow up for agent - {who_agent} today")

    # formatted_queue = [
    #     {"agent_id": s.agent_id, "account_id":  s.account_id, "customer_name": s.customer_name, "overdue_amount": s.overdue_amount, "overdue_days":  s.overdue_days, "risk_level": s.risk_level, "product_type": s.product_type}
    # for s in all_overdue_list if s.get("agent_id") == who_agent]
    agent_name = state_list[2].agent_name
    print(f"\nQueue for Agent - {who_agent}/({agent_name}) - {len(all_overdue_acc_sorted)} accounts total:")
    print('-' * 90)
    # print_lines = []
    # for i, text in enumerate(all_overdue_acc_sorted, start = 1):
    #     # print_lines.append(
    #     print(f"{i}. {text.get('account_id')} | {text.get('customer_name'):<20} | INR {text.get('overdue_amount'):>8} | {text.get('overdue_days'):>3} days | {text.get('product'):<15} | Risk {risk(text.get('overdue_days'))}")
    #     current_state.risk_level =risk(text.get('overdue_days'))

    for i, state in enumerate(state_list, start = 1):
        if state.agent_id == who_agent:
        # print_lines.append(
            print(f"{i}. {state.account_id} | {state.customer_name:<20} | INR {state.overdue_amount:>8} | {state.overdue_days:>3} days | {state.product_type:<15} | Risk {(state.risk_level)}")
        # current_state.risk_level =risk(text.get('overdue_days'))
    print('-' * 90)

    # # print(f"\n{print_lines}")
    # which_account = input("\nwhich Account details you want to display: ")
    # agent_account_summary(state_list, all_accounts_list, which_account, who_agent)

def agent_account_summary(state_list: list[ConversationState], account_id: str)-> str:
    """
    read v3_accounts.json and v3_call_log.json and returns a formatted summary for the agent
    """

    # print(all_accounts_list)
    for acc in state_list:
        if acc.account_id == account_id:
            return_statement = (
            f"\nAccount        :- {acc.account_id}"
            f"\nCustomer       :- {acc.customer_name}"
            f"\nCustomer Phone :- {acc.phone}"
            f"\nProduct        :- {acc.product_type}"
            f"\nOverdue        :- {acc.overdue_amount} - overdue for {acc.overdue_days} days"
            f"\nLast Payment   :- {acc.last_payment_amount} Dated- {acc.last_payment_date}"
            f"\nRisk Level     :- {acc.risk_level}"
            f"\nNotes          :- {acc.notes}"
        )
            # agent_account_brief(return_statement, account_id, agent_id)
            return(return_statement)

def agent_account_brief(account_summary: str):
    """this gets data from agent account_summary and using llm it converts in into human form"""
    PROMPT = """you are collection copilot assitant for a bank.
    you receive a structured account details and converts them into :
    1. A natural language summary of the customer's situation
    2. A suggested approach for the collection Agent
    3. Key talking points of the call
    
    Be concise, professional and action-oriented.
    Never invent information not provided
    Format: summary paragraph, then Suggested approach section 
   """

    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": account_summary}]
    print(chat(messages))

def agent_extract_promise(user_message: str )-> dict:
    """Extract promise amount and date date from the user message and 
    return {'promise_amout:' float, 'date:' str}"""
    prompt = f"""
    Today's date is {datetime.now().strftime('%Y-%m-%d')}.
    Extract the payment promise details from this message
    return on valid two fields in strict json format and no other value
    "amount": the promised payment amount as number
    "date:" the promised date in DD-MON-YYYY format
    If the agent says "today" → use {datetime.now().strftime('%Y-%m-%d')}
    If the agent says "tomorrow" → use {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
    If the agent says "Friday" → calculate the next Friday from today
    If date is unclear → use ""    if no date or amount mentioned then return 'No updates from customer'
    
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
    llm_extract = llm_output[start_index:end_index]
    print(llm_extract)
    llm_extract_dict = json.loads(llm_extract)# since this is str so converting it to dict
    return(llm_extract_dict)
    print('-' * 70)

def build_prompt_ask_llm(question: str) -> str:
    """user question sent to llm"""
    # context = "\n\n".join(context_chunks)
    messages = [
        {"role": "system", "content": "Answer questions from the intent recived:"},
        {"role": "user", "content": {question}}
    ]
    return chat(messages)    
    
def main():
    tee_stream = start_tee(__file__)
    now = datetime.now()
    print('=' * 70)
    print(f"Copilot started @{now}")
    print('=' * 70)
    who = input("\n Enter your Agent-id please : ")
    # while True:
    #     user_imput = input("Please write your query (or type 'quit' to exit):")
    #     if user_imput.lower() == "quit":
    #         print("Exiting the application - Goodbye")
    #         break
    #     classify_intent(user_imput)
    with open(ACCOUNT_FILE_PATH, "r") as acc_file_reader:
        accounts_details = json.load(acc_file_reader)
    with open(CALLLOG_FILE_PATH, "r") as call_log_file_reader:
        call_logs = json.load(call_log_file_reader)
    with open(AGENT_FILE_PATH, "r") as agent_file_reader:
        agent_details = json.load(agent_file_reader)
    # create a lookup on call log file
    call_log_lookup = {item["account_id"]: item for item in call_logs} # fetch reported balance Step 2
    # create a lookup on agent file
    agent_lookup = {item["agent_id"]: item for item in agent_details} # fetch reported balance Step 2

    
    all_state = []
    for account in accounts_details:
        acnt_id = account.get('account_id')
        agent_id = call_log_lookup.get(acnt_id, {}).get("agent_id")
        notes = call_log_lookup.get(acnt_id, {}).get("notes")
        agent_profile = agent_lookup.get(agent_id, {})
        daily_logs = agent_profile.get("daily_logs", [])
        total_promise_to_pay = sum (day.get("promises_to_pay") for day in daily_logs)
        # fetcing all details
        matching_calls = call_log_lookup.get(acnt_id, {})
        # print(f"\n promise_date: {matching_calls.get('promise_date')} ")
        # 4. Calculate risk_level:
        #    overdue_days > 90 → "critical"
        #    overdue_days > 60 → "urgent"
        #    otherwise         → "normal"

         # ------------------------------------------
        # Create state
        # ------------------------------------------
        static_data = {
            "session_id": "001",
            "agent_id": agent_id,
            "agent_name": agent_lookup.get(agent_id, {}).get("agent_name"),
            # "agent_name":  agent_lookup.get(agent_id, {}).get("agent_name"),
            # ── Account details ────────────────────────────────
            "account_id": acnt_id,
            "customer_name": account.get('customer_name'),
            "phone": account.get("phone"),
            "product_type": account.get("product"),
            # ── Financial position ─────────────────────────────
            "overdue_amount": account.get("overdue_amount"),
            "overdue_days": account.get("overdue_days"),
            "last_payment_date": account.get("last_payment_date"),
            "last_payment_amount": account.get("last_payment_amount"),
            "notes": notes,
            # ── Promise to pay ─────────────────────────────────
            "promise_amount": matching_calls.get("promise_amount"),
            "promise_date": matching_calls.get("promise_date") or "",
            # ── Risk classification ────────────────────────────
            "risk_level":  ("Critical" if (account.get("overdue_days") or 0) > 90  
                            else "Urgent" if (account.get("overdue_days") or 0) > 60  
                            else "Normal")
        }
        current_state = ConversationState(**static_data)
        all_state.append(current_state)
        # account_details = agent_account_summary(current_state)
    agent_show_queue(all_state, who)

    # print(f"\n{print_lines}")
    which_account = input("\nwhich Account details you want to display: ")
    account_summary = agent_account_summary(all_state, which_account)
    account_message = agent_account_brief(account_summary)
    agent_input = input("\nPlease mention user's response: ")
    llm_extract = agent_extract_promise(agent_input)
    # new_log_final = {}
    new_log = None   # ← define before the loop
    # --------------------------------------------------
    # update the promise in call log
    # --------------------------------------------------
    customer_name = ""
    for state in all_state:
        if state.account_id == which_account and state.agent_id == who:
            state.promise_amount = llm_extract.get("amount")
            customer_name = state.customer_name
            state.promise_date   = llm_extract.get("date")
            state.action_taken   = "log_promise"
            state.log_date       = datetime.now().isoformat()
            new_log = {
                "log_id"    : f"LOG{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "account_id": which_account,
                "date"      : datetime.now().strftime("%Y-%m-%d"),
                "agent_id"  : who,
                "outcome": "promise_to_pay",
                "promise_amount": state.promise_amount,
                "promise_date": state.promise_date,
                "notes": agent_input
            }
            # new_log_final = new_log
            # break   # ← stop once found

            if new_log is None:
                print(f"Account {which_account} not found for agent {who}")
                
            try:
                with open(CALLLOG_FILE_PATH, "r") as calllog_file_reade:
                    call_logs = json.load(calllog_file_reade)
            except (json.JSONDecodeError, FileNotFoundError):
                call_logs = []   # start fresh if file empty or missing        

            call_logs.append(new_log)
            with open(CALLLOG_FILE_PATH, "w") as calllog_file_write:
                json.dump(call_logs, calllog_file_write, indent=4)
            print(f"Promise logged for {which_account} INR {state.promise_amount} date {state.promise_date} Follow-up scheduled for {state.promise_date}")
            print('-' * 70)
            print(f"PAYMENT History for - {which_account}/{customer_name}")
            print('-' * 70)
            for log in call_logs:
                if which_account == log.get("account_id"):
                    print(f"{log.get('date')} | description = {log.get('notes') or log.get('outcome', '')} | by {log.get('promise_date')} | {log.get('agent_id')}")
            final_agent_comments = input(f"\nUpdate your comments {who}: ")
            agent_intent = classify_intent(final_agent_comments)
            if agent_intent == "escalate":
                print("searching for pilicy document ..... wait pannu ma\n")
                # --------------------------------------------------
                # RAG - Embedding Function starts
                # --------------------------------------------------
                # initiate_chroma_client(db_path)

                with open(POLICY_FILE_PATH, "r") as f:
                    policy_text = f.read()


                build_over = build_knowledge_base(initiate_chroma_client(db_path), policy_text)
                print(build_over)
                # Step 1 — retrieve escalation policy via RAG
                results = build_over.query(
                    query_embeddings = embed(["legal escalation criteria overdue collections"]),
                    n_results        = 2,
                    include          = ["documents"]
                )
                policy_context = "\n".join(results["documents"][0])
                print(f"\n Policy Context - {policy_context}")
                total_promises = sum(1 for log in call_logs if log.get("outcome") == "promise_to_pay")
                print(f"\n total promises - {total_promises}")
                criteria_met = (
                    state.overdue_days > 90 and 
                    state.overdue_amount > 50000
                    and total_promises > 2
                )

                # update state
                if criteria_met:
                    state.escalate_to_legal = True
                    state.action_taken = "escalated"

                prompt = f"""
                Account: {state.account_id} - {state.customer_name}
                Overdue: INR {state.overdue_amount:,.0f} for {state.overdue_days} days
                Contact attempts: {total_promises}
                Criteria met: {criteria_met}
                Policy: {policy_context}

                Explain the escalation decision to the collections agent in 2-3 sentences.
                If criteria not met, explain what is still needed.
                """
                messages = [
                        {"role": "system", "content": "You are a collections policy assistant."},
                        {"role": "user",   "content": prompt}
                    ]
                llm_suggestion = chat(messages)
                print(llm_suggestion)

    # print(current_state)
    # print(f"the Intent is - {classify_intent(user_imput)}")
    now = datetime.now()
    print('=' * 70)
    print(f"Copilot quit @{now}")
    print('=' * 70)
    stop_tee(tee_stream)

if __name__ == "__main__":
    main()
