"""
BFSI AI Compliance Officer — Production Scale
Handles 10,000+ transactions with:
  - Chunked processing (100 at a time)
  - Checkpointing after every chunk
  - Resume from failure
  - One LLM call for final report
"""

import os
import json
import config
from openai import OpenAI
from datetime import datetime
from tee_logger import start_tee, stop_tee
from collections import Counter
from pathlib import Path
from pydantic import BaseModel, Field

CURR_PATH = Path(__file__).parent
TRANSACTIONS_FILE_NAME = "v1_transactions.json"
TRANSACTIONS_FILE_PATH = CURR_PATH.joinpath(TRANSACTIONS_FILE_NAME)
POSITIONS_FILE_NAME = "v1_positions.json"
POSITIONS_FILE_PATH = CURR_PATH.joinpath(POSITIONS_FILE_NAME)
LIMITS_FILE_NAME = "v1_limits.json"
LIMITS_FILE_PATH = CURR_PATH.joinpath(LIMITS_FILE_NAME)
EPISODIC_JSON_FILE = CURR_PATH.joinpath("v1_episodic_file.json")

CHUNK_SIZE = 100 # process only 100 records one time
CHECKPOINT_FILE_PATH = CURR_PATH.joinpath("v1_checkpoint.json")
RESULTS_FILE_PATH = CURR_PATH.joinpath("v1_results_file.json")
PROMPT = """YOU are a banking and financial AI agent, 
you take output from :
1. data quality agent,
2. reconciliation agent 
3. regulatory agent 
4. rule_reference

and prepare a one page Executive summary for CRO/CFO/Regulators
Requirements: 
- Formal and precise tome
- no unnecessary jargon 
- action orientd 
- Clearly identify important issues
- Do not invent information
- Base the report only on the provided agent outputs"""
client = OpenAI(api_key = os.getenv("GEMINI_API_KEY"), base_url = os.getenv("GEMINI_BASE_URL"))

class ComplianceState(BaseModel):
    #  ---------transactions details---------
    trxn_id: str
    trxn_date: str
    trxn_account: str
    trxn_amount: float
    trxn_currency: str
    trxn_type: str
    # ---------account level details---------
    acc_reported_balance: float
    acc_exposure_limit: float
    # ---------quality details---------
    quality_score: float = 0.0 #calculated as round(1.0 - (len(issues) / 5), 2) = round(1.0 - 2/5) = 0.6
    quality_issues: list = Field(default_factory=list)
    # ---------reconciliation details---------
    recon_matched_yn: bool = True
    recon_diference: float = 0.0
    recon_type: str = "" # (matched, un-matched, currency mismatch)
    # ---------regulatory details---------
    limit_breached: bool = False
    breach_amount: float = 0.0 # how much over the limit
    compliance_status: str = "" #"compliant" / "breach" / "warning"
    regulatory_rules: str = "RBI Circular 2024/47"
    # ---------llm summary level details---------
    report_summary: str = ""

# ------------------------------------------------------------------
# File check
# ------------------------------------------------------------------
def check_validity_of_datafiles()-> str:
    """check if files exists and raise error"""
    path_to_check = {
        "transactions": Path(TRANSACTIONS_FILE_PATH),
        "positions": Path(POSITIONS_FILE_PATH),
        "limits": Path(LIMITS_FILE_PATH)}
    files_status = []
    try:
        for name, path in path_to_check.items():
            if not path.is_file():
                raise FileNotFoundError(f"Missing file - {name} at {path}")
            files_status.append(f"{name} - Success")
    except FileNotFoundError as e:
        print(f"Check files - configuration error - {e}")
        raise
    except Exception as e:
        print(f"There is problem in one of the file - {e}")
    # print(files_status)
    return files_status

def get_chunks(transactions_list: list, chunk_size: int) -> list[list]:
    """processing transactions into chukcs of 100 each time - 1000 = 9 chunks"""
    chunks = []
    start = 0
    while start < len(transactions_list):
        end = start + chunk_size
        chunks.append(transactions_list[start: end])
        start += chunk_size  # FIXED: Increment start to move to the next chunk
        # print("\n The Next chunk is .............")
        # print(transactions_list[start: end])
    return chunks

def agent_data_quality(state, all_trxn_list: list[str]) -> ComplianceState:
   """This function validates qulatity of every record and updates ComplianceState"""
   issues = []
   state.quality_score = 1

   if state.trxn_amount == 0.0 and state.trxn_type in ["credit", "debit"]:
      issues.append("Null_amount")

   if state.trxn_amount is None:
      issues.append("Null_amount")

   if abs(state.trxn_amount - state.acc_reported_balance) > 1000000:
      # "Transaction Id {all_trxn_list} has {state.amount} <0 - needs to be checked".append(f"Transaction Id {all_trxn_list} has reported balance low {state.acc_reported_balance} than {state.amount} 0 - needs to be checked")
      issue_1 = "Reconciliation_break"
      issues.append(issue_1)

   if state.trxn_amount < 0 and state.trxn_type == 'credit':
      
      issue_1 = "Sign_error"
      issues.append(issue_1)

   if state.trxn_currency != 'INR':
      issue_1 = ("Currency_mismatch")
      issues.append(issue_1)

   if all_trxn_list.count(state.trxn_id) > 1:
    issues.append("Duplicate_record")

   state.quality_score  = round(1.0 - (len(issues) / 5), 2)
   state.quality_issues = issues
#    print(f"\n Issues are - {issues}")
   return state

def agent_reconciliation_check(state: ComplianceState) -> ComplianceState:
   """Function to check the reconciliation for each account"""
    # 1. amounts match exactly → recon_matched=True, recon_flag="matched"
   difference = abs(state.trxn_amount - state.acc_reported_balance)

   if difference == 0:
      state.recon_matched_yn = True
      state.recon_diference = 0
      state.recon_type = "matched"
   elif difference < 1000000:
      state.recon_matched_yn = False
      state.recon_diference = difference
      state.recon_type = "minor difference"
   else:
      state.recon_matched_yn = False
      state.recon_diference = difference
      state.recon_type = "un-matched"
   return state

    # 2. difference <= 1000000 → recon_matched=True, recon_flag="minor_variance"  
    # 3. difference > 1000000 → recon_matched=False, recon_flag="unmatched"
    #    also set recon_difference = abs(amount - reported_balance)

def agent_regulatory(state: ComplianceState) -> ComplianceState:
   """this function checks against the limits"""
   # 1. amount <= limit → limit_breached=False, compliance_status="compliant"
   amount = state.trxn_amount
   limit = state.acc_exposure_limit

   if amount <= limit:
      state.limit_breached = False
      state.compliance_status = "compliant"
      state.breach_amount = 0.0
    # 2. amount > limit but < limit * 1.1 → limit_breached=True, 
    #    compliance_status="warning", breach_amount = amount - limit
   if amount > limit * 1.1:
      state.limit_breached = True
      state.compliance_status = "warning"
      state.breach_amount =  amount - limit
    # 3. amount > limit * 1.1 → limit_breached=True,
    #    compliance_status="breach", breach_amount = amount - limit
   else:
      state.limit_breached = True
      state.compliance_status = "breach"
      state.breach_amount = abs(state.trxn_amount) - state.acc_exposure_limit

   if state.trxn_amount ==0:
      state.limit_breached = True
      state.compliance_status = "compliant"
      state.breach_amount = 0.0
   return state

def aggregate_stat_result(state: list[ComplianceState]) -> dict:
    """agrregates all data from state for reporting"""
    issue_counter = Counter()
    for s in state: issue_counter.update(s.quality_issues)
    return {
       "total_transaction": len(state),
       "quality_issues_found": sum(1 for s in state if s.quality_issues),
       "recon_breaks": sum(1 for s in state if s.recon_type == "un-matched"),
       "limit_breachs": sum(1 for s in state if s.limit_breached),
       "breach_accounts": [s.trxn_account for s in state if s.limit_breached],
       "top_issues":  issue_counter.most_common(5),
       "total_breach_amount": sum(s.breach_amount for s in state),
       "high_risk_accounts": [s.trxn_account for s in state if s.quality_score < 0.6]
    }

# ------------------------------------------------------------------
# report generation creation
# ------------------------------------------------------------------
def agent_generate_report_llm(state: ComplianceState, summary: str) -> str:
   """it takes output from all other agents and genearte a one page report for CRO/CFO/Regulators"""
   prompt = f""" You are recieving a batch of {len(state)} financial transactions processed by automated compliance agents
   BATCH RESULTS: {json.dumps(summary, indent=2)}

             Prepare a one-page executive summary for CRO/CFO/Regulators covering:
1. Total transactions reviewed
2. Data quality issues found
3. Reconciliation breaks
4. Regulatory breaches requiring action
5. Recommended immediate actions
"""
   reponse = client.chat.completions.create(model = os.getenv("GEMINI_MODEL_NAME"),
                                            messages = [
                                               {"role": "system", "content": PROMPT},
                                               {"role": "user", "content": prompt}
                                            ], temperature = 0.7)
   report = reponse.choices[0].message.content
   return report

# ------------------------------------------------------------------
# transactions handling
# ------------------------------------------------------------------
def agent_transaction_handling() -> str:
    """it reads all the transactions from file and process them and skips if they already processed"""
    transactions_list = []

    # ------------------------------------------------------------------
    # Lookup for positions
    # ------------------------------------------------------------------
    with open(POSITIONS_FILE_PATH, "r") as positions_file_reader: # fetch reported balance Step 1
        all_positions = json.load(positions_file_reader)
    positions_lookup = {item["account"]: item for item in all_positions} # fetch reported balance Step 2

    # ------------------------------------------------------------------
    # Lookup for limits
    # ------------------------------------------------------------------
    with open(LIMITS_FILE_PATH, "r") as limits_file_reader:
        all_limits = json.load(limits_file_reader)
    limits_lookup = {item["account"]: item for item in all_limits}

    # ------------------------------------------------------------------
    # episodoc memory handling
    # ------------------------------------------------------------------
    processed_trxn_id = []
    try:
        with open(EPISODIC_JSON_FILE, "r") as episodic_file_read:
            processed_trxn_id = json.load(episodic_file_read)
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error in episodic file, File may be empty - {e}")
        processed_trxn_id = []

    # ------------------------------------------------------------------
    #  create a fast lookup for episodic trxn id
    # ------------------------------------------------------------------
    episodic_lookup = {item["trxn_id"]: item for item in processed_trxn_id}

    with open(TRANSACTIONS_FILE_PATH, "r") as trxn_file_reader:
        all_transactions_in_ram = json.load(trxn_file_reader)
        all_trxn_id = [transactions["txn_id"] for transactions in all_transactions_in_ram]
        trxn_counts = Counter(all_trxn_id)
    # ------------------------------------------------------------------
        # get chunks of all the transactions
    # ------------------------------------------------------------------
        all_chunks = get_chunks(all_transactions_in_ram, CHUNK_SIZE)
        # print(f"\n {all_chunks}")
        compliance_states = []
        
        # for i in all_transactions_in_ram[:5]: # only 5 records for now
        for index, chunk in enumerate(all_chunks, start = 1):
            print(f"--- Processing Chunk {index} (Size: {len(chunk)}) records ---")
        
            for transaction in chunk:
                if transaction.get("txn_id") in episodic_lookup:
                    print(f"\n transaction id - {transaction.get("txn_id")} already been processed - bring new data to process")
                else:
                    account_id = transaction.get("account")
                    reported_balance = (positions_lookup.get(account_id, {})).get("reported_balance") # fetch reported balance Step 3
                    account_limit    = limits_lookup.get(account_id, {}).get("limit")
                    trans = {"trxn_id": transaction.get("txn_id"), "trxn_date": transaction.get("date"), "account_balance": reported_balance, "account max limit": account_limit}
                    # transactions_list.append(trans)
                    static_data = {
                        "trxn_id"       : transaction.get("txn_id"),
                        "trxn_date"     : transaction.get("date"),
                        "trxn_account"  : transaction.get("account"),
                        "trxn_amount"   : transaction.get("amount") or 0.0,
                        "trxn_currency" : transaction.get("currency"),
                        "trxn_type"     : transaction.get("type"),
                        "acc_reported_balance" : reported_balance or 0.0,
                        "acc_exposure_limit"   : account_limit or 0.0
                    }
                    current_state_instance = ComplianceState(**static_data)
                    # ------------------------------------------------------------------
                    # Agents pipelines
                    # ------------------------------------------------------------------
                    quality_agent = agent_data_quality(current_state_instance, all_trxn_id)
                    recon_agent = agent_reconciliation_check(current_state_instance)
                    regulatory_agent = agent_regulatory(current_state_instance)

                    # ------------------------------------------------------------------
                    # Stores successful state
                    # ------------------------------------------------------------------
                    compliance_states.append(current_state_instance)
                    processed_trxn_id.append(trans)

                    # print(f"Processing new transaction - {trans}")
                    # total_records_in_state = aggregate_stat_result(compliance_states)
                    # print(f"\n Total nof of records in compliance state are - {total_records_in_state}")
            # saving checkpoint data 
            with open(CHECKPOINT_FILE_PATH, "w") as checkpoint_file_writer:
                json.dump({"last_chunk": index}, checkpoint_file_writer, indent = 4)
            # print(transactions_list)
            with open(EPISODIC_JSON_FILE, "w") as episodic_file_write:
                json.dump(processed_trxn_id, episodic_file_write, indent = 4)
        # ----------------------------------------------
        # Final aggregation
        # ----------------------------------------------
        summary = aggregate_stat_result(compliance_states)
        llm_report = agent_generate_report_llm(compliance_states, summary)
        print(llm_report)
        return transactions_list

def main():
    tee_stream = start_tee(__file__)
    now = datetime.now()
    print('=' * 70)
    print(f"Execution of script started @ {now}")
    print('=' * 70)
    file_state = check_validity_of_datafiles()
    # print(file_state)
    transaction_handling = agent_transaction_handling()
    # print(transaction_handling)
    now = datetime.now()
    print('=' * 70)
    print(f"Execution of script stopped @ {now}")
    print('=' * 70)
    stop_tee(tee_stream)

if __name__ == "__main__":
    main()