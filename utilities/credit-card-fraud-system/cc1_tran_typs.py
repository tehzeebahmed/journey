"""This is part of the credit card fraud detection system"""
import os
import json
import chromadb
from tee_logger import start_tee, stop_tee
from pydantic import BaseModel
from pathlib import Path
from google import genai
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

class customEmbeddingFunction(EmbeddingFunction):
    def __init__(self) -> None:
        self.client = genai.Client("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_EMBEDDING_MODEL")
    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return[]

        embeddings = []
        for text in input:
            response = self.client.models.embed_content(
                model = self.model_name, content = text
            )
            embeddings.append(response.embeddings[0].values)
        return embeddings

class transactionRecord(TypedDict):
    id_transaction:           str
    customer_id:              str
    amount_transaction:       float
    merchant_name:            str
    merchant_transaction:     str
    device_used:              str
    payment_tran_type:        str
    fraud_signal:             bool
    fraud_risk_score:         float

class frauddetyect(TypedDict):
    customer_id:              str
    fraud_score:              float
    prev_dispute_counts:      int
    suspecious_flag:          bool

class merchantDet(TypedDict):
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

class DisputeRecord(TypedDict):
    dispute_id:               str
    customer_id:              str
    transaction_id:           str
    dispute_amount:           float
    dispute_reason:           str
    transaction_date:         str
    merchant:                 str
    dispute_status:           str

class DisputeState(TypedDict):
    dispute_id:               str
    customer_id:              str
    transaction_id:           str
    dispute_amount:           float
    dispute_reason:           str
    transaction_date:         str
    merchant:                 str
# From Agent 1
    transaction_data: dict
# from agent 2
    fraud_data: dict
# from agent 3
    merchant_data: dict
# from RAG
    policy_context: str
# Supervisior decision
    decision: str
    reason: str
    poilicy_ref: str


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

def agent_get_transaction(db_file_path: str, search_value: Union[str, int, float]) -> transactionRecord:
    """Agent 1 — Transaction Agent,  Input: transaction_id, Looks up transaction in transactions_db.json, Returns: transaction details + risk signals (new device? unusual time? unusual location?)"""
    try:
        with open(db_file_path, "r", encoding='utf-8') as file:
            
            data = json.load(file)
            for record in data:
                if record.get("transaction_id") == search_value:
                    print(f" the Transaction ID  {record.get('transaction_id')} -  {record.get('amount')} has a record for {search_value}")
                    return {
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
                
            print(f"Transaction ID {search_value} was not found in the dataset.")
            return None
    except (FileNotFoundError, json.JSONDecodeError):
        print("inside except agent 1")
        return None
def agent_fraud_signal(fraud_db_file:str, custId: str):
    """Agent 2 - Fraud agent with Input: customer_id,  Looks up customer in fraud_patterns_db.json and Returns: fraud score, previous dispute count, suspicious flag"""
    try:
        with open(fraud_db_file, 'r', encoding = 'utf-8') as file:
            fraud_data = json.load(file)
            for record in fraud_data:
                if record.get("customer_id") == custId:
                    return{
                        "customer_id":  record.get("customer_id"),
                        "fraud_score": record.get("fraud_score"),
                        "prev_dispute_counts": record.get("previous_disputes"),
                        "suspecious_flag": record.get("suspicious_flag")
                    }
            print("\nNo fraud history detected for {custId} - boy seems clean.")
            return None    
    except (FileNotFoundError, json.JSONDecodeError):
            print("inside except Agent 2")
            return None

def Agent_merchant_details(merchant_df_file: str, mrchntname: str):
    """Agent 3 — Merchant Agent, Input: merchant name, Looks up merchant in merchants_db.json and Returns: dispute rate, trusted status, fraud complaint count"""
    try:
        with open(merchant_df_file, 'r', encoding = 'utf-8') as file:
            merchant_data = json.load(file)
            for record in merchant_data:
                if record.get("merchant") == mrchntname:
                    return{
                        "merchant_name": record.get("merchant"),
                        "merchant_id": record.get("merchant_id"),
                        "dispute_rate": record.get("dispute_rate"),
                        "trusted_status": record.get("trusted"),
                        "fraud_complaint_count": record.get("fraud_complaints")
                    }
            print(f"\n No data found for this merchant - {mrchntname}")
            return None
    except (FileNotFoundError, json.JSONDecodeError):
                print("inside except Agent 3")
                return None

def agent_get_dispute(disputedb: str, custId: str, originalTrxn_id: str):
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
    print(f"We are searching data in {TRN_FILE_FULL_PATH}")
    disputed_transaction = agent_get_transaction(TRN_FILE_FULL_PATH, ORIG_TRXN_ID)
    print(f"\nagent got transactions for transaction - {ORIG_TRXN_ID}")
    print('='*60)
    print(f"\nThe output of record {disputed_transaction}")
    if disputed_transaction is not None:
        customer_id_for_fraud_analysis = disputed_transaction["customer_id"]
        merchant_name_for_fraud_analysis = disputed_transaction["merchant_name"]
        fraud_data = agent_fraud_signal(FRD_FILE_FULL_PATH, customer_id_for_fraud_analysis)
        print('='*60)
        print(f"\nCustomer - {customer_id_for_fraud_analysis} analyzed by agent and here is the fraud data - ")
        print(fraud_data)
        merchant_data = Agent_merchant_details(MRCHNT_FILE_FULL_PATH, merchant_name_for_fraud_analysis)

        print('='*60)
        print(f"\nMerchant details collected by Agent 3 (merchant Agent) for - {merchant_name_for_fraud_analysis}")
        print(merchant_data)
        dispute_data = agent_get_dispute(DISPUTE_FILE_FULL_PATH, customer_id_for_fraud_analysis, ORIG_TRXN_ID)
        print('='*60)
        print(f"\n Dispute data found for {ORIG_TRXN_ID} - and customer {customer_id_for_fraud_analysis}")
        print(dispute_data)
        print('='*60)
    else:
        print("\nCould not analyze fraud signals by agent 2 because the transaction record was not found.")
    #  now the chunking 
    with open(DISPUTE_POLICYFILE_FULL_PATH, "r") as file:
        file_content = file.read()
        chunks = chunks_by_section(file_content)
        print(chunks)

    stop_tee(tee_stream)

if __name__ == "__main__":
    main()

