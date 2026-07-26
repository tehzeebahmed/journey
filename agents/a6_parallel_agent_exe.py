"""
Supervisor Pattern
Loan underwriting: supervisor + 3 parallel specialist agents

Run all three using ThreadPoolExecutor in parallel

with concurrent.futures.ThreadPoolExecutor() as executor:
    credit_future   = executor.submit(credit_agent,   state).  → starts immediately 
    fraud_future    = executor.submit(fraud_agent,    state).  → starts immediately 
    property_future = executor.submit(property_agent, state).  → starts immediately 

# all three run at the same time
# collect results when all finish
credit_result   = credit_future.result().                      → waits for credit to finish
fraud_result    = fraud_future.result()                        → waits for fraud to finish 
property_result = property_future.result()                     → waits for property to finish
"""

import os
import json
from pathlib import Path
from tee_logger import start_tee, stop_tee
import concurrent.futures
from typing_extensions import TypedDict
from mistralai.client import Mistral
from datetime import datetime
class LoanState(TypedDict):
    applicant_name :  str
    pan_number:        str
    monthly_salary:   float
    phone:            str
    property_address: str
    property_value:  float
    loan_amount:      float
    credit_score:     int
    faud_flag:        bool
    decision:         str
    reason:           str

CURR_PATH = Path(__file__).parent

CREDIT_DB_FILE_PATH = CURR_PATH.joinpath("a6_fake_credit_scores.json")
FRAUD_DB_FILE_PATH = CURR_PATH.joinpath("a6_fake_fraud_data.json")
PROP_DB_FILE_PATH = CURR_PATH.joinpath("a6_fake_property_addr_value.json")
PROP_APPL_FILE_PATH = CURR_PATH.joinpath("a6_fake_loan_appl.json")
print (f"The credit data file is - {CREDIT_DB_FILE_PATH}")
print (f"The Fraud data file is - {FRAUD_DB_FILE_PATH}")
print (f"The property data file is - {PROP_DB_FILE_PATH}")
print (f"The Application data file is - {PROP_APPL_FILE_PATH}")

with open (PROP_APPL_FILE_PATH, "r") as file:
    APPL_DB = json.load(file)
    PAN_LOOKUP_DB = {app["pan_number"]: app for app in APPL_DB}
    record_count = len(APPL_DB)
    print({record_count})
    print(type(APPL_DB))  # Output: <class 'list'>

# ── Worker 1: Credit Agent ─────────────────────────────────────────────────────
def credit_agent(state: LoanState) -> dict:
    """look up credit score from CREDIT_DB using pan_number"""
    print(f"Worker 1 - Credit agent was called at - {datetime.now()}")

    pan = state["pan_number"]
    profile = PAN_LOOKUP_DB.get(pan) # Get None if not found
    if profile is None:
        #   return default values or raise an error
        print(f"Warning: PAN {pan} not found in DB.")
        return {"credit_score": 0} # Or appropriate d
    credit_score = profile.get("credit_score", 0) # Now profile is a dict or None, handled above
    # print(f"Credit Agent - worker 1 - credit score for pan {pan} - {credit_score}")
    
    return {"credit_score": credit_score}

# ── Worker 2: Fraud Agent ─────────────────────────────────────────────────────
def fraud_agent(state: LoanState) -> dict:
    """look up Fraud flag from json DB using pan_number"""
    print(f"\nWorker 2 - Fraud agent was called at - {datetime.now()}")
    pan = state["pan_number"]
    profile = PAN_LOOKUP_DB.get(pan,0)
    fraud_flag = profile.get("fraud_flag")
    return {"fraud_flag": fraud_flag} 


# ── Worker 3: property Agent ─────────────────────────────────────────────────────
def property_agent(state: LoanState) -> dict:
    """look up property value from json DB using pan number"""
    print(f"\nWorker 3 - Credit agent was called at - {datetime.now()}")
    pan = state["pan_number"]
    profile = PAN_LOOKUP_DB.get(pan,0)
    property_value = profile.get("property_value")
    return  {"property_value": property_value}    # return dict to update state

def supervisor(state: LoanState)-> LoanState:
    """
    Run all three workers in parallel.
    Collect results. Make decision.
    """
    print("\n[Supervisor] Starting parallel checks...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        credit_future   = executor.submit(credit_agent,   state)  
        fraud_future    = executor.submit(fraud_agent,    state) 
        property_future = executor.submit(property_agent, state)

        # all three run at the same time
        # collect results when all finish
        credit_result   = credit_future.result()
        fraud_result    = fraud_future.result()
        property_result = property_future.result()

    # update state with worker results
    state["credit_score"]   = credit_result["credit_score"]
    state["fraud_flag"]     = fraud_result["fraud_flag"]
    state["property_value"] = property_result["property_value"]
    property_value =  state["property_value"] 
    if property_value == 0:
        state["decision"] = "Rejected"
        state["reason"] = "Property value cannot be zero for LTV calculation."
        return state
    # calculate LTV
    ltv = (state["loan_amount"] / state["property_value"]) * 100
    
    # print("Value:", state["credit_score"], "Type:", type(state["credit_score"]))

    if int(state["credit_score"]) < 650:
        state["decision"]= "Rejected"
        state["reason"] = "credit score below minimum threshold of 650"
    elif state["fraud_flag"] == True:
        state["decision"]= "Rejected"
        state["reason"] = "Frad Detected at PAN"
    elif ltv > 80:
        state["decision"]= "Rejected"
        state["reason"] = f"LTV ratio {ltv:.1f}% exceeds maximum 80%"
    else:
        # if all checks passed then approve
        state["decision"]= "Approved"
        state["reason"] = "Loan application has approved - congratulations"
    return state

def main():
    """main function - get all details from json file using PAN and pass to AgentState"""
    tee_stream= start_tee(__file__)
    with open (PROP_APPL_FILE_PATH, "r") as file:
            APPL_DB = json.load(file)
    pan_number = input("\nEnter your PAN No here - ")    
    # 2. Map PAN number to the entire dictionary object
    PAN_LOOKUP_DB = {app["pan_number"]: app for app in APPL_DB}

    profile = PAN_LOOKUP_DB.get(pan_number)
    if not profile:
        print(f"[MAIN SECTION] - PAN {pan_number} does not ecists")
    
    state1 = {
        "applicant_name":   profile["applicant_name"],
        "pan_number":              pan_number,
        "monthly_salary":   profile["monthly_salary"],
        "phone":            profile["phone"],
        "property_address": profile["property_address"],
        "loan_amount":      profile["loan_amount"],
        "credit_score":     profile["credit_score"],
        "fraud_flag":       profile["fraud_flag"],
        "property_value":   profile["property_value"],
        "decision":         "",
        "reason":           ""
    }

    for state in [state1]:
        result = supervisor(state)
        print(f"\n{'='*60}")
        print(f"Applicant    : {result['applicant_name']}")
        print(f"Credit Score : {result['credit_score']}")
        print(f"Fraud Flag   : {result['fraud_flag']}")
        print(f"Property Val : INR {result['property_value']:,}")
        ltv = (result['loan_amount'] / result['property_value']) * 100
        print(f"LTV Ratio    : {ltv:.1f}%")
        print(f"DECISION     : {result['decision'].upper()}")
        print(f"Reason       : {result['reason']}")
        print('='*60)
    stop_tee(tee_stream)
    print(f"\n\nExecution of Script Ended at {datetime.now()}")
if __name__ == "__main__":
    main()


"""
### Flow of the Script

Here's the step-by-step flow of the corrected script:

**Step 1: Initialization and Data Loading (Script Start)**
*   The script starts execution.
*   `Path` objects are created for all data files.
*   **`a6_fake_loan_appl.json` is loaded once into `APPL_DB` and then processed into `PAN_LOOKUP_DB` (a dictionary mapping PAN numbers to applicant profiles). This `PAN_LOOKUP_DB` is made available globally for agents.**
*   Constants like `MIN_CREDIT_SCORE` and `MAX_LTV_PERCENTAGE` are defined.

**Step 2: Main Function Execution (`main()` called)**
*   **`start_tee(__file__)`** is called to begin logging output to both console and a file.
*   The user is prompted to enter a PAN number.
*   The entered PAN is used to look up the applicant's profile from the **global `PAN_LOOKUP_DB`**.
*   **Error Handling:** If the PAN is not found, an error message is printed, and the script exits.
*   If found, an initial `LoanState` dictionary (`state1`) is created for the applicant. Key fields like `credit_score`, `fraud_flag`, `property_value`, `decision`, and `reason` are initialized to default values (e.g., `0`, `False`, `""`) as they will be populated by the agents.

**Step 3: Supervisor Orchestration (`supervisor(state)` called)**
*   The `supervisor` function receives the `LoanState` for the current applicant.
*   It prints a message indicating the start of parallel checks.
*   **`concurrent.futures.ThreadPoolExecutor()`** is initialized.
*   **Parallel Agent Submission:**
    *   `executor.submit(credit_agent, state)`: The `credit_agent` function is submitted to the thread pool, starting its execution in a separate thread immediately. It receives the `LoanState`.
    *   `executor.submit(fraud_agent, state)`: The `fraud_agent` function is submitted, starting immediately.
    *   `executor.submit(property_agent, state)`: The `property_agent` function is submitted, starting immediately.
    *   These three agents run concurrently.

**Step 4: Agent Execution (in parallel threads)**
*   Each agent (`credit_agent`, `fraud_agent`, `property_agent`):
    *   Prints a timestamped message indicating it was called.
    *   Retrieves the `pan_number` from the received `LoanState`.
    *   **Performs a lookup in the global `PAN_LOOKUP_DB` using the PAN.**
    *   **Includes error handling for PAN not found.**
    *   Extracts its specific data point (`credit_score`, `fraud_flag`, `property_value`) from the profile.
    *   Returns a dictionary containing its result (e.g., `{"credit_score": 720}`).

**Step 5: Supervisor Result Collection and Decision Making**
*   Back in the `supervisor` function:
    *   `credit_future.result()`: The supervisor waits for the `credit_agent` thread to complete and retrieves its result.
    *   `fraud_future.result()`: Waits for `fraud_agent` and retrieves its result.
    *   `property_future.result()`: Waits for `property_agent` and retrieves its result.
*   The `LoanState` object is updated with the results from all three agents.
*   **Error Handling:** It checks if `property_value` is zero to prevent `ZeroDivisionError` during LTV calculation.
*   The LTV (Loan-to-Value) ratio is calculated.
*   A series of conditional checks are performed to determine the loan `decision` and `reason`:
    *   If `credit_score` is below `MIN_CREDIT_SCORE`.
    *   If `fraud_flag` is `True`.
    *   If LTV is above `MAX_LTV_PERCENTAGE`.
    *   If all checks pass, the loan is `Approved`.
*   The updated `LoanState` (with decision and reason) is returned.

**Step 6: Main Function Output and Cleanup**
*   Back in `main()`:
    *   The `result` (the final `LoanState` from the supervisor) is used to print a formatted summary of the loan application, including the credit score, fraud flag, property value, calculated LTV, decision, and reason.
*   **`stop_tee(tee_stream)`** is called to stop logging and close the tee file.
*   A final message indicating the end of script execution is printed.

---
"""