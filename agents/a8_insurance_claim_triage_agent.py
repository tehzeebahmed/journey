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
from typing import Optional
from datetime import datetime
from tee_logger import start_tee, stop_tee
from pydantic import BaseModel, Field

CLAIMS = [
    {
        "claim_id":    "CLM001",
        "customer_id": "CUST101",
        "claim_type":  "vehicle_accident",
        "amount":      45000,
        "description": "Car rear-ended at signal. Damage to bumper and boot."
    },
    {
        "claim_id":    "CLM002",
        "customer_id": "CUST202",
        "claim_type":  "theft",
        "amount":      180000,
        "description": "Laptop and jewellery stolen from home. FIR filed."
    },
    {
        "claim_id":    "CLM003",
        "customer_id": "CUST303",
        "claim_type":  "medical",
        "amount":      12000,
        "description": "Hospitalised for 2 days. Fever and dehydration."
    }
]

FRAUD_SCORES:  float = {"CUST101": 0.2, "CUST202": 0.85, "CUST303": 0.4}
PLOICY_LIMIT: float = {"vehicle_accident": 50000, "theft": 100000, "medical": 25000}
DECISION:     str   = {"approved", "investigate", "rejected"}

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

def supervisior(fraud_score: float, claim_amount: float, policy_amount: float) -> str:
    """this is the fiomnal engine to decide the action on the claim"""
    # print(fraud_score)
    # print(claim_amount)
    # print(policy_amount)
    if fraud_score < 0.5 and claim_amount < policy_amount:
        return("All good boy - Claim passed - Approved")
    elif fraud_score < 0.5 and claim_amount > policy_amount:
        return(f"Lets investigate - farud score is within limit but claim anount {claim_amount} exceeds policy {policy_amount}")
    else:
        return(f"Rejected - the claim amount {claim_amount} exceeds policy limit {policy_amount} and fraud score is {fraud_score}")
    # return None


def main():
    tee_stream = start_tee(__file__)
    right_now = datetime.now()
    print('=' * 60)
    print(f"\n Script execution started @ - {right_now}")

    for record in CLAIMS:
        state = claimState(**record)
        state.claim_id = record.get("claim_id")
        state.customer_id = record.get("customer_id")
        # print(state.customer_id)
        state.claim_type = record.get("claim_type")
        state.amount = record.get("amount")
        state.description = record.get("description")
        state.fraud_score = record.get("fraud_score")
        state.policy_limit = record.get("policy_limit")
        state.decision = record.get("decision")
        # state.reason = record.get("description")
        
        returned_score = fraud_agent(state)

        policy_amount = policy_agent(state)
        # print(f"\n the tmaximum amount for {state.claim_type} is {policy_amount}")
        # print( returned_score)
        current_state = state
        # print(current_state)

        final_call = supervisior(returned_score, state.amount, policy_amount)
        print(f"\n Cusomer - {state.customer_id} 's claim {state.claim_id} for amount {state.amount} - {final_call}")

    right_now = datetime.now()
    print('=' * 60)
    print(f"\n Script execution ended @ - {right_now}")
    stop_tee(tee_stream)

if __name__ == "__main__":
    main()
