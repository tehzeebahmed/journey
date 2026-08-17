"""positions generation engine"""
import json
import random
from pathlib import Path

CURR_PATH = Path(__file__).parent
POSITIONS_FILE = "rag9_positions.json"
POSITIONS_FILE_PATH = CURR_PATH.joinpath(POSITIONS_FILE)

# 1. Base template matching requirements
positions = [
    {"account": "ACC001", "reported_balance": 450000,  "currency": "INR"},
    {"account": "ACC002", "reported_balance": 280000,  "currency": "INR"},
    {"account": "ACC003", "reported_balance": 9500000, "currency": "INR"},
    {"account": "ACC004", "reported_balance": 92000,   "currency": "INR"}
]

# 2. Loop to build up to 20,000 records
for i in range(5, 20001):
    account_id = f"ACC{i:03d}"
    
    # Generate realistic tiered balances
    balance = random.choices(
        [random.randint(5000, 100000), random.randint(100001, 1000000), random.randint(1000001, 15000000)],
        weights=[40, 50, 10]
    )[0]
    
    # Inject rare data gaps (nulls) every 200 records for pipeline robustness testing
    if i % 200 == 0:
        balance = None
        
    currency = random.choice(["INR", "NOK", "INR", "GBP", "INR", "USD", "EUR"]) if balance is not None else "INR"
    
    positions.append({
        "account": account_id,
        "reported_balance": balance,
        "currency": currency
    })

# 3. Write to local JSON file
with open(POSITIONS_FILE_PATH, "w") as f:
    json.dump(positions, f, indent=2)
