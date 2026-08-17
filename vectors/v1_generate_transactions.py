"""Generate synthetic transactions data"""
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

# Define constants
CURR_PATH = Path(__file__).parent
TRANSACTION_FILE = "rag9_transactions.json"
TRANSACTION_FILE_PATH = CURR_PATH.joinpath(TRANSACTION_FILE)
BASE_DATE = datetime(2026, 8, 10)
ACCOUNTS = [f"ACC{i:03d}" for i in range(1, 150)]
CURRENCIES = ["INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR", "INR"] # Heavily weight INR

# Start building records
records = []

# 1. Add the exact example records requested to guarantee explicit scenario matches
records.append({"txn_id": "T001", "account": "ACC001", "amount": 450000, "currency": "INR", "type": "credit", "date": "2026-08-10"})
records.append({"txn_id": "T002", "account": "ACC002", "amount": None, "currency": "INR", "type": "debit", "date": "2026-08-10"})
records.append({"txn_id": "T003", "account": "ACC003", "amount": 12500000, "currency": "USD", "type": "credit", "date": "2026-08-11"})
# The exact duplicate record
records.append({"txn_id": "T001", "account": "ACC001", "amount": 450000, "currency": "INR", "type": "credit", "date": "2026-08-10"})
records.append({"txn_id": "T004", "account": "ACC004", "amount": -85000, "currency": "INR", "type": "credit", "date": "2026-08-12"})

# Generate remaining 995 records up to 1000 total
for i in range(5, 1000):
    txn_id = f"T{i:03d}"
    account = random.choice(ACCOUNTS)
    tx_type = random.choice(["credit", "debit"])
    
    # Simulate a few missing amounts (None) randomly (~3% chance)
    if random.random() < 0.03:
        amount = None
    else:
        # Most amounts are positive, a few negative anomalies (~1% chance)
        if random.random() < 0.01:
            amount = -1 * random.randint(5000, 100000)
        else:
            amount = random.randint(1000, 2000000)
            
    # Simulate a few wrong currencies (USD, EUR, GBP) randomly (~2% chance)
    if random.random() < 0.02:
        currency = random.choice(["USD", "EUR", "GBP", "NOK"])
    else:
        currency = "INR"
        
    # Generate dates around August 2026
    date_offset = random.randint(0, 4)
    date_str = (BASE_DATE + timedelta(days=date_offset)).strftime("%Y-%m-%d")
    
    records.append({
        "txn_id": txn_id,
        "account": account,
        "amount": amount,
        "currency": currency,
        "type": tx_type,
        "date": date_str
    })

# Save file to disk
with open(TRANSACTION_FILE_PATH, "w") as f:
    json.dump(records, f, indent=2)

print(f"Generated {len(records)} records successfully.")
