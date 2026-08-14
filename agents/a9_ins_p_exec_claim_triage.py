"""
A customer submits an insurance claim. Your agent reads it, classifies it, checks fraud risk, and decides: auto-approve, investigate, or reject.
1. Claim input
2. ClaimState
3. Two agents running in parallel:
   - fraud_agent(state) — looks up fraud score from a hardcoded dict
   - policy_agent(state) — looks up policy limit for the claim type from a hardcoded dict
4. Supervisor decision rules:
    IF fraud_score > ???         → rejected
    IF amount > policy_limit     → investigate
    IF ???                       → approved
5. Process all 3 claims in a loop   
"""
import json
from typing import Optional
from datetime import datetime
import concurrent.futures
from tee_logger import start_tee, stop_tee
from pydantic import BaseModel, Field
from pathlib import Path
CURR_PATH = Path(__file__).parent
CUS_FRAUD_SCORES = "a9_customer_fraud_scores.json"
CUS_FRAUD_SCORES_PATH = CURR_PATH.joinpath(CUS_FRAUD_SCORES)
CUS_PEND_CLAIMS = "a9_pending_claims.json"
CUS_PEND_CLAIMS_PATH = CURR_PATH.joinpath(CUS_PEND_CLAIMS)
PLOICY_LIMIT = "a9_policy_limits.json"
PLOICY_LIMIT_PATH = CURR_PATH.joinpath(PLOICY_LIMIT)
DECISION:     str   = {"approved", "investigate", "rejected"}

with open(CUS_PEND_CLAIMS_PATH, "r") as file:
    CLAIMS = json.load(file)
with open(CUS_FRAUD_SCORES_PATH, 'r') as file:
    FRAUD_SCORES = json.load(file)
with open(PLOICY_LIMIT_PATH, "r") as file:
    PLOICY_LIMIT = json.load(file)

class claimState(BaseModel):
    claim_id:     str   = Field(description= " Claim ID")
    customer_id:  str   = Field(description= "customer who filed insurance claim")
    claim_type:   str   = Field(description= "claim type like theft, medical")
    amount:       float = Field(description= "Amount claimed")
    description:  str   = Field(description= "Claim description")
    # reason:       Optional[str] = Field(description= "The reason")
    fraud_score:  Optional[float] = Field(default=None, description="Calculated fraud score for this customer")
    policy_limit: Optional[float] = Field(default=None, description="Policy limit for this specific claim type")
    decision:     Optional[str]   = Field(default=None, description="Final status: approved, investigate, or rejected")

def fraud_agent(state):
    """This function searched fraud_score dict and retuens value"""
    customerid = state.customer_id
    # print(f"\the customer id inside the agent is - {customerid}")
    score = FRAUD_SCORES.get(state.customer_id)
    # print(f"\n the fraud Score for customer {customerid} is {score}")
    return score

def policy_agent(state):
    """this agent looks up into the policy and pass the max claim anount"""
    claim_type = state.claim_type
    policy_amount = PLOICY_LIMIT.get(claim_type)
    return policy_amount

def supervisor(state) -> str:
    """this is the fiomnal engine to decide the action on the claim"""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        print(datetime.now())
        policy_amount = executor.submit(policy_agent, state)
        print(datetime.now())
        fraud_score = executor.submit(fraud_agent, state)

        #collecting results
        fraud_score_result = fraud_score.result()
        policy_amount_result = policy_amount.result()

    if fraud_score_result > 0.7:
        return f"Rejected — high fraud score {fraud_score_result}"
    elif state.amount > policy_amount_result:
        return f"Rejected — amount {state.amount} exceeds policy limit {policy_amount_result}"
    elif fraud_score_result < 0.5 and state.amount <= policy_amount_result:
        return "Approved — all checks passed"
    else:
        return "Investigate — borderline case"


def main():
    tee_stream = start_tee(__file__)
    right_now = datetime.now()
    print('=' * 60)
    print(f"\n Script execution started @ - {right_now}")

    for record in CLAIMS:
        state = claimState(**record)
        current_state = state
        # print(current_state)

        final_call = supervisor(current_state)
        print(f"\n Cusomer - {state.customer_id} 's claim {state.claim_id} for amount {state.amount} - {final_call}")

    right_now = datetime.now()
    print('=' * 60)
    print(f"\n Script execution ended @ - {right_now}")
    stop_tee(tee_stream)

if __name__ == "__main__":
    main()
