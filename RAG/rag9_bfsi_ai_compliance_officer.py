
"""
BFSI AI compliance officer
"""
import os
import json
import config
# from llm_router import chat
from openai import OpenAI
from tee_logger import start_tee, stop_tee
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
CURR_PATH = Path(__file__).parent
EPISODIC_JSON_FILE = CURR_PATH.joinpath("rag9_episodic_file.json")

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

TRANSACTIONS = [
  {"txn_id": "T001", "account": "ACC001", "amount": 450000, "currency": "INR", "type": "credit", "date": "2026-08-10"},
  {"txn_id": "T002", "account": "ACC002", "amount": None,   "currency": "INR", "type": "debit",  "date": "2026-08-10"},
  {"txn_id": "T003", "account": "ACC003", "amount": 12500000,"currency": "USD","type": "credit", "date": "2026-08-11"},
  {"txn_id": "T001", "account": "ACC001", "amount": 450000, "currency": "INR", "type": "credit", "date": "2026-08-10"},
  {"txn_id": "T004", "account": "ACC004", "amount": -85000, "currency": "INR", "type": "credit", "date": "2026-08-12"}
]

POSITIONS = [
  {"account": "ACC001", "reported_balance": 450000,  "currency": "INR"},
  {"account": "ACC002", "reported_balance": 280000,  "currency": "INR"},
  {"account": "ACC003", "reported_balance": 9500000, "currency": "INR"},
  {"account": "ACC004", "reported_balance": 92000,   "currency": "INR"}
]

LIMITS = [
  {"account": "ACC001", "limit": 500000,   "type": "single_counterparty"},
  {"account": "ACC002", "limit": 300000,   "type": "single_counterparty"},
  {"account": "ACC003", "limit": 10000000, "type": "large_exposure"},
  {"account": "ACC004", "limit": 75000,    "type": "retail_credit"}
]

class ComplianceState(BaseModel):
    # Inputs from raw files ---------
    txn_id:        str
    account:       str
    amount:        float = 0.0
    currency:      str
    type:          str
    reported_balance:  float
    exposure_limit:    float
    # Agent 2 - data quality ---------
    quality_score:     float     = 0.0
    quality_issues:   list[str] = [] # ["null amount", "wrong currency"]
    # Agent 3 - reconciliation ---------
    recon_matched:     bool      = True 
    recon_difference:  float     = 0.0 # how much it doesn't match
    recon_flag:        str       = "" # "matched" / "unmatched" / "currency_mismatch"
    # Agent 4 - Regulatory ---------
    limit_breached:    bool      = False 
    breach_amount:     float     = 0.0 # how much over the limit
    rule_difference:   str       = "" # "RBI Circular 2024/47"
    complaince_status: str       = "" #"compliant" / "breach" / "warning"
    # Agent 5 - LLM report Summary ---------
    report_summary:    str       = "" # LLM based report executed summary in 100 words

def agent_data_quality(state, all_trxn_list: list[str]) -> ComplianceState:
   """This function validates qulatity of every record and updates ComplianceState"""
   issues = []
   state.quality_score = 1

   if state.amount == 0.0 and state.type in ["credit", "debit"]:
      issues.append("Null_amount")
      
   if abs(state.amount - state.reported_balance) > 1000000:
      # "Transaction Id {all_trxn_list} has {state.amount} <0 - needs to be checked".append(f"Transaction Id {all_trxn_list} has reported balance low {state.reported_balance} than {state.amount} 0 - needs to be checked")
      issue_1 = "Reconciliation_break"
      issues.append(issue_1)
# return state
   if state.amount < 0 and state.type == 'credit':
      
      issue_1 = "Sign_error"
      issues.append(issue_1)

   if state.currency != 'INR':
      issue_1 = ("Currency_mismatch")
      issues.append(issue_1)

   if all_trxn_list.count(state.txn_id) > 1:
    issues.append("Duplicate_record")

   state.quality_score  = round(1.0 - (len(issues) / 5), 2)
   state.quality_issues = issues

   return state
def agent_reconciliation_check(state: ComplianceState) -> ComplianceState:
   """Function to check the reconciliation for each account"""
    # 1. amounts match exactly → recon_matched=True, recon_flag="matched"
   if state.amount == state.reported_balance:
      state.recon_matched = True
      state.recon_difference = 0
      state.recon_flag = "matched"
   if state.reported_balance - state.amount > 1000000:
      state.recon_matched = False
      state.recon_difference = state.reported_balance - state.amount
      state.recon_flag = "minor difference"
         
   if state.reported_balance - state.amount >= 1000000:
      state.recon_matched = False
      state.recon_difference = state.reported_balance - state.amount
      state.recon_flag = "un-matched"

    # 2. difference <= 1000000 → recon_matched=True, recon_flag="minor_variance"  
    # 3. difference > 1000000 → recon_matched=False, recon_flag="unmatched"
    #    also set recon_difference = abs(amount - reported_balance)
def agent_regulatory(state: ComplianceState) -> ComplianceState:
   """this function checks against the limits"""
   # 1. amount <= limit → limit_breached=False, compliance_status="compliant"
   if state.amount <= state.exposure_limit:
      state.limit_breached = False
      state.complaince_status = "compliant"
      state.breach_amount = 0.0
    # 2. amount > limit but < limit * 1.1 → limit_breached=True, 
    #    compliance_status="warning", breach_amount = amount - limit
   if state.amount > state.exposure_limit and (state.exposure_limit - state.amount) < state.exposure_limit * 1.1:
      state.limit_breached = True
      state.complaince_status = "warning"
      state.breach_amount =  abs(state.amount)  - state.exposure_limit
    # 3. amount > limit * 1.1 → limit_breached=True,
    #    compliance_status="breach", breach_amount = amount - limit
   if (state.exposure_limit - state.amount) > state.exposure_limit * 1.1:
      state.limit_breached = True
      state.complaince_status = "breach"
      state.breach_amount = abs(state.amount) - state.exposure_limit

   if state.amount ==0:
      state.limit_breached = True
      state.complaince_status = "compliant"
      state.breach_amount = 0.0
def agent_generate_report_llm(state: ComplianceState) -> str:
   """it takes output from all other agents and genearte a one page report for CRO/CFO/Regulators"""
   # total_trxns = len(state.txn_id)
   batch_summary = []
   for s in state:
        batch_summary.append({
            "txn_id":           s.txn_id,
            "account":          s.account,
            "quality_issues":   s.quality_issues,
            "quality_score":    s.quality_score,
            "recon_flag":       s.recon_flag,
            "compliance":       s.complaince_status,
            "breach_amount":    s.breach_amount
        })
   prompt = f""" You are recieving a batch of {len(state)} financial transactions processed by automated compliance agents
   BATCH RESULTS: {json.dumps(batch_summary, indent=2)}

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
def main():
    tee_stream = start_tee(__file__)
    now = datetime.now()
    print(f"Script Execution Started @{now}")
    compliance_states: list[ComplianceState] = []  # <-- 1. Initialize list before loop
    
    # ---------------------------------------------------------
    # 1. Load episodic memory
    # ---------------------------------------------------------
    processed_transaction = []
    try:        
      with open(EPISODIC_JSON_FILE, "r") as file_reader:
         processed_transaction = json.load(file_reader)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
    # This runs if the file is empty (JSONDecodeError) or doesn't exist yet (FileNotFoundError)
      print(" File is empty or missing. Starting with an empty transaction list.")
      processed_transaction = []
    # ---------------------------------------------------------
    # 2. Create a set of already processed transaction IDs
    # ---------------------------------------------------------
    processed_transaction_ids = {item.get("txn_id") for item in processed_transaction if item.get("txn_id") is not None}

    compliance_states: list[ComplianceState] = []
    # ---------------------------------------------------------
    # 3. Create lookup dictionaries
    # ---------------------------------------------------------
    # creating a lookup for positions
    positions_lookup = {item["account"]: item for item in POSITIONS}
    limits_lookup = {item["account"]: item for item in LIMITS}

    # All transaction IDs - used by Data Quality Agent
    all_txn_ids = [r["txn_id"] for r in TRANSACTIONS]

    # ---------------------------------------------------------
    # 4. Process transactions
    # ---------------------------------------------------------
    for record in TRANSACTIONS:
        acnt_id = record.get("account")
        transaction_date = record.get("date")
        trxn = record.get("txn_id")
        # -----------------------------------------------------
        # Check episodic memory
        # -----------------------------------------------------
        if trxn in processed_transaction_ids:
            print(f"Transaction {trxn} already processed Skipping.")
            continue
        else:

         # print(f"\nProcessing {trxn} dated {transaction_date} for account {acnt_id}")

            # -----------------------------------------------------
            # 5. Lookup position and exposure limit
            # -----------------------------------------------------
         matching_positions = positions_lookup.get(acnt_id, {})
         exposure_limit = limits_lookup.get(acnt_id, {})

            # state = ComplianceState(**record)
            # -----------------------------------------------------
            # 6. Build ComplianceState input
            # -----------------------------------------------------
         static_data = {
            "txn_id"   : record.get("txn_id"),
            "account"  : acnt_id,
            "amount"   : record.get("amount") or 0.0,
            "currency"  : record.get("currency"),
            "type"     : record.get("type"),
            "reported_balance": matching_positions.get("reported_balance", 0.0),
            "exposure_limit"  : exposure_limit.get("limit", 0.0)
            }
            #   print(processed_transaction)
            #   print(f"\nthe ids are \n{processed_transaction}")
            # -----------------------------------------------------
            # 7. Run compliance agents
            # -----------------------------------------------------
         try:
               state_instance = ComplianceState(**static_data)
               # compliance_states.append(state_instance)
               quality_check = agent_data_quality(state_instance, all_txn_ids)
               recon_state = agent_reconciliation_check(state_instance)
               agent_regulatory(state_instance)
               rule_reference = "RBI Large Exposure Guidelines 2023"

               # Append state to our batch collection
               compliance_states.append(state_instance)

               # print(f"{state_instance.txn_id} | score: {state_instance.quality_score} | issues : {state_instance.quality_issues}")
               print(f"{state_instance.txn_id} | Quality score: {state_instance.quality_score} | Quality issues : {state_instance.quality_issues} - {state_instance.txn_id} | rcon: {state_instance.recon_flag} | compliance : {state_instance.complaince_status} | breach: {state_instance.breach_amount}")
               # print(generate_report)
               # print(f"\n the state for account {acnt_id} is : {state_instance}")
               # -------------------------------------------------
               # 8. Add transaction to episodic memory
               # -------------------------------------------------
               formatted_transaction = {"txn_id": trxn, "date": transaction_date}
               processed_transaction.append(formatted_transaction)
               processed_transaction_ids.add(trxn)
         except Exception as e:
               print(f"Validation Error mapping account {acnt_id}: {e}")
         # if compliance_states:
         #    generate_report = agent_generate_report_llm(state_instance)
         #    print(generate_report)
         # else:
         #    print("no transaction porocessed yet")
    # ---------------------------------------------------------
    # 9. Write episodic memory AFTER processing all transactions
    # ---------------------------------------------------------
    with open(EPISODIC_JSON_FILE, "w") as f:
            json.dump(processed_transaction, f,indent=4)
   # ---------------------------------------------------------
    # 10. Generate ONE report for the full batch
    # ---------------------------------------------------------
    if compliance_states:
        generate_report = agent_generate_report_llm(compliance_states)  # ← pass full list
        print("\n" + "="*60)
        print("EXECUTIVE COMPLIANCE REPORT")
        print("="*60)
        print(generate_report)
    else:
        print("No new transactions processed.")

    now = datetime.now()
    print(f"Script Execution Endeded @{now}")
    stop_tee(tee_stream)

if __name__ == "__main__":
    main()