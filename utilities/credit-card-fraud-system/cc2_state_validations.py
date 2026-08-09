"""This is part of the credit card fraud detection system"""
import os
import json
import chromadb
import config
from tee_logger import start_tee, stop_tee
from pydantic import BaseModel, Field
from pathlib import Path
from google import genai
from typing import Optional
import concurrent.futures
from typing_extensions import TypedDict, List, Union
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

CURR_DIR = Path(__file__).parent
TRN_DB_FILE = "transactions_db.json"
FRD_DB_FILE = "fraud_patterns_db.json"
MRCHNT_DB_FILE = "merchant_db.json"
DISPUTE_DB_FILE = "dispute_db.json"
DISPUTE_POLICY_FILE = "dispute_policies.txt"
TRN_FILE_FULL_PATH = CURR_DIR.joinpath(TRN_DB_FILE)
FRD_FILE_FULL_PATH = CURR_DIR.joinpath(FRD_DB_FILE)
MRCHNT_FILE_FULL_PATH = CURR_DIR.joinpath(MRCHNT_DB_FILE)
DISPUTE_FILE_FULL_PATH = CURR_DIR.joinpath(DISPUTE_DB_FILE)
DISPUTE_POLICYFILE_FULL_PATH = CURR_DIR.joinpath(DISPUTE_POLICY_FILE)

#ChromaDB details
DB_PATH = "./local_vectordb"
COLLECTION_NAME = "disputeCollection"
# print(f" Transaction database file is at - {TRN_FILE_FULL_PATH}")
api_key = os.getenv("GEMINI_API_KEY")

class customEmbeddingFunction(EmbeddingFunction):
    def __init__(self) -> None:
        self.client = genai.Client(api_key = api_key)
        self.model_name = os.getenv("GEMINI_EMBEDDING_MODEL")
    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return[]

        embeddings = []
        for text in input:
            response = self.client.models.embed_content(
                model = self.model_name, contents = text
            )
            embeddings.append(response.embeddings[0].values)
        return embeddings

class initializationResponse(BaseModel):
    dispute_id:           str
    customer_id:          str
    transaction_id:       str
    dispute_amount:       float
    dispute_reason:       str
    transaction_date:     str
    merchant:             str
    
class transactionResponse(BaseModel):
    id_transaction:           str= Field(validation_alias="transaction_id") 
    customer_id:              str
    amount_transaction:       float
    merchant_name:            str
    merchant_transaction:     str
    device_used:              str
    payment_tran_type:        str
    fraud_signal:             bool
    fraud_risk_score:         float

class fraudResponse(BaseModel):
    customer_id:              str
    fraud_score:              float
    prev_dispute_counts:      int
    suspecious_flag:          bool

class merchantResponse(BaseModel):
    merchant_name:            str
    merchant_id:              str
    dispute_rate:             float
    trusted_status:           bool
    fraud_complaint_count:    int

class masterTransaction(TypedDict):
    """WE MAY NOT NEED THIS ONE"""
    master_transaction_id:    str
    master_customer_id:       str
    master_transaction_value: float

class DisputeRecord(BaseModel):
    dispute_id:               str
    customer_id:              str
    transaction_id:           str
    dispute_amount:           float
    dispute_reason:           str
    transaction_date:         str
    merchant:                 str
    dispute_status:           str

class DisputeState(BaseModel):
    dispute_id:               str
    customer_id:              str
    transaction_id:           str
    dispute_amount:           float
    dispute_reason:           str
    transaction_date:         str
    merchant:                 str
   # Storage slots for three agents and supervisor (agent memory)
    transaction_data: dict = Field(default_factory= dict) # From Agent 1
    fraud_data:       dict = Field(default_factory= dict) # from agent 2
    merchant_data:    dict = Field(default_factory= dict) # from agent 3
    policy_context:   str  = " "              # from RAG
    decision:         str  = "pending"        # Supervisior decision
    reason:           str  = ""               # Supervisior decision
    policy_ref:      str   = ""               # Supervisior decision

def initiate_chromadb_instance():
    """initializing chromadb instance"""
    print("\n Initializing chroma db....wait for few seconds..")
    return chromadb.PersistentClient(path=DB_PATH)

# Chunking 
def chunks_by_section(text: str) -> list[str]:
    """Split on section headers — semantic chunking."""
    import re
    sections = re.split(r'\n\n(?=Section \d+)' , text)
    return[s.strip() for s in sections if s.strip()]
    # return sections 

def supervisor(state: DisputeState, collection: chromadb.Collection) -> DisputeState:
    """Acts as supervisor - collects data from agents and make decisions"""

    initial_results_validated = initializationResponse(
        dispute_id=state.dispute_id,
        customer_id=state.customer_id,
        transaction_id=state.transaction_id,
        dispute_amount=state.dispute_amount,
        dispute_reason=state.dispute_reason,
        transaction_date=state.transaction_date,
        merchant=state.merchant
    )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        transx_state = executor.submit(agent_get_transaction,           state,  TRN_FILE_FULL_PATH)
        fraudx_state = executor.submit(agent_fraud_signal,              state, FRD_FILE_FULL_PATH)
        mercht_state = executor.submit(Agent_merchant_details,          state, MRCHNT_FILE_FULL_PATH)

        # Wait for all threads to finish updating the object state        
        transx_state.result()
        fraudx_state.result()
        mercht_state.result()

        #Now validating with pydantic structure
        if state.transaction_data:
            transxx_state_validated = transactionResponse(**state.transaction_data)
        state.transaction_data = transxx_state_validated.model_dump()

        if state.fraud_data:
            fraudxx_state_validated = fraudResponse(**state.fraud_data)
            state.fraud_data = fraudxx_state_validated.model_dump()

        if state.merchant_data:
            merchtx_state_validated = merchantResponse(**state.merchant_data)
            state.merchant_data = merchtx_state_validated.model_dump()
            
        # state["initial_data"] = initial_results_validated.model_dump()
        # state["transaction_data"] = transxx_state_validated.model_dump()
        # state["fraud_data"]       = fraudxx_state_validated.model_dump()
        # state["merchant_data"]   = merchtx_state_validated.model_dump()

        #decision logic
        fraud_score  = state.fraud_data.get("fraud_score", 0)
        dispute_rate = state.merchant_data.get("dispute_rate", 0)
        prev_dispute = state.fraud_data.get("prev_dispute_counts", 0)

        if state.dispute_amount > 50000:
            state.decision = "escalated"
            state.reason = "Amount exceeds INR 50,000 — human review required"
        elif prev_dispute > 3:
            state.decision = "rejected"
            state.reason = "Customer has more than 3 previous disputes"
        elif dispute_rate > 0.05:
            state.decision = "refund"
            state.reason = "Merchant dispute rate exceeds 5% — ruling in customer favour"
        elif fraud_score > 0.7:
            state.decision = "refund"
            state.reason = "High fraud score detected — refund approved"
        else:
            state.decision = "refund"
            state.reason   = "All checks passed — refund approved"

        policy_results = collection.query(
        query_texts=[f"{state.dispute_reason} {state.dispute_amount}"],
        n_results=2 )

        if policy_results.get("documents") and len(policy_results["documents"]) > 0:
            state.policy_context = "\n".join(policy_results["documents"][0])
        
        return state

        # update state with worker results
                # Step 4 — update state from validated objects  ← see here dot notation, not dict keys
        # state["credit_score"]   = credit_validated.credit_score

def initialize_state_by_dispute_id(disputeId: str, disputrdbFile: str) -> Optional[DisputeState]:
    """supplied the dispute id and it will fetch the transaction no and subsequently other details"""
    try:
        with open(disputrdbFile, "r", encoding='utf-8') as file:
            
            data = json.load(file)
            for record in data:
                if record.get("dispute_id") == disputeId:
                    print(f"\nFound record for Dispute ID  {record.get('dispute_id')}")
                    return DisputeState (
                        dispute_id = record.get("dispute_id"), customer_id=record.get("customer_id"),
                        transaction_id = record.get("transaction_id"), dispute_amount = record.get("disputed_amount"),
                        dispute_reason = record.get("dispute_reason"), transaction_date = record.get("transaction_date"),
                        merchant = record.get("merchant")
                    )
            print(record.get("transaction_id"))
            return None
            print(f"\nDispute ID {disputeId} not found in the database ...")
    except (FileNotFoundError, json.JSONDecodeError):
            print("inside except Agent 2")
            return None
        
def agent_get_transaction(state: DisputeState, db_file_path: str) -> DisputeState:
    """Agent 1 — Transaction Agent,  Input: transaction_id, Looks up transaction in transactions_db.json, Returns: transaction details + risk signals (new device? unusual time? unusual location?)"""
    try:
        with open(db_file_path, "r", encoding='utf-8') as file:
            
            data = json.load(file)
            for record in data:
                if record.get("transaction_id") == state.transaction_id:
                    print(f" the Transaction ID  {record.get('transaction_id')} -  {record.get('amount')} has a record for {state.transaction_id}")
                    state.transaction_data = {
                        # Transaction details fetched
                        "transaction_id": record.get("transaction_id"),
                            "customer_id": record.get("customer_id"),
                            "amount_transaction": record.get("amount"),
                            "merchant_name": record.get("merchant"),
                            "merchant_transaction": record.get("merchant"),
                            "device_used": record.get("device"),
                            "payment_tran_type": record.get("payment_method"),
                            #risk details also fetched
                            "fraud_signal": record.get("is_fraud"),
                            "fraud_risk_score": record.get("risk_score")}
                    return state
            print(f"Transaction ID {state.transaction_id} was not found in the dataset.")
            return None
    except (FileNotFoundError, json.JSONDecodeError):
        print("inside except agent 1")
        return None
def agent_fraud_signal(state: DisputeState, fraud_db_file:str) -> DisputeState:
    """Agent 2 - Fraud agent with Input: customer_id,  Looks up customer in fraud_patterns_db.json and Returns: fraud score, previous dispute count, suspicious flag"""
    # custId = state["customer_id"]
    try:
        if not os.path.exists(fraud_db_file):
            print(f"\n fraud database file missing ....... ")
            return state
        
        with open(fraud_db_file, 'r', encoding = 'utf-8') as file:
            fraud_data = json.load(file)

            for record in fraud_data:
                if record.get("customer_id") == state.customer_id:
                    #update the state with value state.fraud_data dict
                    state.fraud_data = {    
                        "customer_id":  record.get("customer_id"),
                        "fraud_score": record.get("fraud_score"),
                        "prev_dispute_counts": record.get("previous_disputes"),
                        "suspecious_flag": bool(record.get("suspicious_flag"))
                    }
                    return state
            print(f"\nAgent 2 - No fraud history detected for {state.customer_id} - boy seems clean.")
            # Safe return
            state.fraud_data = {"customer_id": state.customer_id, "fraud_score": 0.0, "prev_dispute_counts": 0, "suspecious_flag": False}
            return state    
    except (FileNotFoundError, json.JSONDecodeError):
            print("inside except Agent 2")
            return None

def Agent_merchant_details(state: DisputeState, merchant_df_file: str) -> DisputeState:
    """Agent 3 — Merchant Agent, Input: merchant name, Looks up merchant in merchants_db.json and Returns: dispute rate, trusted status, fraud complaint count"""
    try:
        with open(merchant_df_file, 'r', encoding = 'utf-8') as file:
            merchant_data = json.load(file)
            for record in merchant_data:
                if record.get("merchant") == state.merchant:
                    state.merchant_data = {
                        "merchant_name": record.get("merchant"),
                        "merchant_id": record.get("merchant_id"),
                        "dispute_rate": record.get("dispute_rate"),
                        "trusted_status": record.get("trusted"),
                        "fraud_complaint_count": record.get("fraud_complaints")
                    }
                    return state
            print(f"\n No data found for this merchant - {state.merchant}")
            return None
    except (FileNotFoundError, json.JSONDecodeError):
                print("inside except Agent 3")
                return None

def agent_get_disputex(disputedb: str, custId: str, originalTrxn_id: str):
    """Agent 4 - Cross-verifies if a dispute record's customer_id and amount exactly match the details in the transaction master file."""
    try:
        with open(disputedb, "r", encoding = 'utf-8') as file:
            dispute_data = json.load(file)
            for record in dispute_data:
                if record.get("transaction_id") == originalTrxn_id and record.get("customer_id") == custId:
                    return {
                        "dispute_id": record.get("dispute_id"),
                        "customer_id": record.get("customer_id"),
                        "transaction_id": record.get("transaction_id"),
                        "dispute_amount": record.get("disputed_amount"),
                        "dispute_reason": record.get("dispute_reason"),
                        "transaction_date": record.get("transaction_date"),
                        "merchant": record.get("merchant"),
                        "dispute_status": record.get("dispute_status")
                    }
            print(f"\nAgent 4 Transaction ID {originalTrxn_id} was not found in the dataset for customer {custId}.")
            return None
    except (FileNotFoundError, json.JSONDecodeError):
        print("inside except of agent 4")
        return None

EMBEDDING_FUNCTION_GEMINI = customEmbeddingFunction()
def build_knowledge_base(client: chromadb.Client, inputStr: str, enb_function: EmbeddingFunction) -> chromadb.Collection:
    """Crating a index and content from policy by sections"""
    
    collection = client.get_or_create_collection(name = COLLECTION_NAME, 
                                     metadata = {"hnsw:space": "cosine"}, # use cosine similarity
                                     embedding_function = EMBEDDING_FUNCTION_GEMINI)  # ChromaDB calls this automatically
    if collection.count() == 0:
        chunks = chunks_by_section(inputStr)
        for i, chunk in enumerate(chunks):
            collection.add(
                ids = [f"chunks_{i}"],         # Unique ID for each individual chunk 
                            #embeddings = [embed(chunks)], # since I am using custom_embedding now no need for this
                            documents = [chunk]            # Each document is a single string chunk
                            )
        print(f"[RAG] Knowledge base ready — {collection.count()} chunks indexed")
    else:
            print(f"[RAG] Collection already has {collection.count()} chunks — skipping index")
    return collection
    

def main(ORIG_TRXN_ID: str = "TXN100002"):
    """Main Engine for fraud detection :)"""
    tee_stream = start_tee(__file__)
    print("\n provide the dispute id:")
    dispute_user_input = input("Dispute ID = ")
    chroma_client = initiate_chromadb_instance()
    with open(DISPUTE_POLICYFILE_FULL_PATH, "r") as file:
        policy_text = file.read()
    collection = build_knowledge_base(chroma_client, policy_text, EMBEDDING_FUNCTION_GEMINI)
    print(f"We are searching data in {TRN_FILE_FULL_PATH}")
    #Fecting data and initializing state  using utility engine Step 1
    current_state = initialize_state_by_dispute_id(dispute_user_input, DISPUTE_FILE_FULL_PATH)
    if current_state:
        print(f"\nDISPIUTE State - transaction id {current_state.transaction_id} fornd for dispute id 'DIS001'")
        print('='*60)
        print(current_state)
        transaction_id_toget_details = current_state.transaction_id
        print('='*60)

        print(f"\nTransaction ID = {transaction_id_toget_details}")
        transaction_state = agent_get_transaction(current_state, TRN_FILE_FULL_PATH)
        print(transaction_state)   
        print('='*60)

        print("Fraud data printing")
        fraud_state = agent_fraud_signal(current_state, FRD_FILE_FULL_PATH)
        print(fraud_state)
        print('='*60)

        print("Merchant details")
        merchant_data = Agent_merchant_details(current_state, MRCHNT_FILE_FULL_PATH)
        print(merchant_data)

        print("Merchant details")
        suoervisor_data = supervisor(current_state, collection)
        print(suoervisor_data)
    stop_tee(tee_stream)

if __name__ == "__main__":
    main()

"""
DIS005 entered
      ↓
initialize_state_by_dispute_id  → DisputeState created
      ↓
Parallel execution:
  Agent 1 (Transaction) ⟐
  Agent 2 (Fraud)       ⟐  → all results written to state
  Agent 3 (Merchant)    ⟐
      ↓
RAG policy search → relevant sections retrieved → state.policy_context
      ↓
Supervisor decision logic → decision + reason written to state
      ↓
Final DisputeState printed with complete audit trail


eature	Status
Four agents running	✅
Pydantic validation	✅
RAG policy lookup	✅
Parallel execution	✅
Decision logic	    ✅ (one bug to fix)
Episodic memory	    ⏭️ add customer dispute history cache
HITL pause	        ⏭️ pause on escalated decisions
Checkpointing	    ⏭️ save state after each agent
main() loop	        ⏭️ ask for next dispute ID after each run
"""