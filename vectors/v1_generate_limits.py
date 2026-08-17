import json
import random
from pathlib import Path

CURR_PATH = Path(__file__).parent
LIMITS_FILE = "rag9_limits.json"
LIMITS_FILE_PATH = CURR_PATH.joinpath(LIMITS_FILE)


# 1. Base template matching your exact core examples
limits_data = [
    {"account": "ACC001", "limit": 500000,   "type": "single_counterparty"},
    {"account": "ACC002", "limit": 300000,   "type": "single_counterparty"},
    {"account": "ACC003", "limit": 10000000, "type": "large_exposure"},
    {"account": "ACC004", "limit": 75000,    "type": "retail_credit"}
]

# 2. Define regulatory categories
types = ["single_counterparty", "large_exposure", "retail_credit", "cross_border"]

# 3. Build mapping up to ACC20000 to cover all system accounts
for i in range(5, 20001):
    account_id = f"ACC{i:03d}"
    
    # Stratify risk categories systematically
    limit_type = random.choices(types, weights=[55, 12, 28, 5], k=1)[0]
    
    # Scale limits dynamically to match potential position ranges
    if limit_type == "large_exposure":
        limit = random.randint(5000000, 25000000)
    elif limit_type == "single_counterparty":
        limit = random.randint(300000, 3000000)
    elif limit_type == "cross_border":
        limit = random.randint(100000, 1500000)
    else:  # retail_credit
        limit = random.randint(15000, 150000)
        
    limits_data.append({
        "account": account_id,
        "limit": limit,
        "type": limit_type
    })

# 4. Save output file locally
output_filename = LIMITS_FILE_PATH
with open(output_filename, "w") as f:
    json.dump(limits_data, f, indent=2)

print(f"Success! Created {output_filename} with {len(limits_data)} records.")
