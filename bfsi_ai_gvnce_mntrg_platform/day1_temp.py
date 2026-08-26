"""
Data contract Schema
it validates a schema changes overtime(versioning of the schema changesO)
"""

import json
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pathlib import Path
from tee_logger import start_tee, stop_tee

CURR_PATH = Path(__file__).parent
INCOMING_TRANSACTIONS_FILE = CURR_PATH.joinpath("gm1_incoming_transactions.json")
CONTRACT_FILE = CURR_PATH.joinpath("gm1_contract.json")

def check_validity_of_files(file_name:str):
    """check file and its associated errors"""
    try:
        if not file_name.exists():
            raise FileNotFoundError(f"\n incoimg transaction file {file_name} is missing entirely")
        print(f"\n***** incoimg transaction file {file_name} is available*****")

        with open(file_name, "r") as file:
            data = json.load(file)
        if len(data) == 0 or not isinstance(data, list):
            raise ValueError("file content is empty or formmat is wrong")
    except FileNotFoundError as e:
        print(f"\nCritical - error - check incoming transactions {e}")
    except json.JSONDecodeError as e:
        print(f"\n malformed json - check incoming stream of transactions data. Line {e.lineno}, Col {e.colno}: {e.msg}")
    except ValueError as e:
        print("Validation Error .....")
    except Exception as e:
        print(f" Unexpected Exception - {e}")    
    return Exception
    
# ----------------column contract schema------------------------
class ColumnContract(BaseModel):
    column_name: str
    data_type:   str              # "string" / "float" / "int" / "bool"
    required:    bool = True
    min_value:      Optional[float] = None
    max_value:      Optional[float] = None
    allowed_values: Optional[list]  = None
    regex_pattern:  Optional[str]  = None

# ---------------- contract schema------------------------
class Datacontract(BaseModel):
    table_name: str
    owner_team: str
    consumer_agents: list[str]
    feed_time: str
    sla_minutes: int
    version: str
    columns: list[ColumnContract]
    
# ---------------- contract valiodation------------------------
class contractViolation(BaseModel):
    table_name: str
    column_name: str
    violation_type: str # null_value/wrong_type/out_of_range/
                        # invalid_enum/new_column/missing_column
    affected_rows: int        # Total no if rows affected
    sample_values: str        # values from incoming record
    severity: str              # Critical/Warning 
    detected_at: str           # Time stamp
    consumer_agents: list[str] # which agent is impacted

def agent_readthru_contract(dataFile: str, state: Datacontract) -> Datacontract:
    """read contract file and pass it on to next agent"""
    with open(dataFile, "r") as dataFile_read:
        contracts_list = json.load(dataFile_read)

    validated_contracts = []
    for pop in contracts_list:
        validated_contracts.append(Datacontract(**pop))
    
    return validated_contracts

def validate_data_against_contract(data: list, contract: Datacontract) -> contractViolation:
    """this agent validate incoming json data against pydantic schema"""    

    # dupliocate check 
    # ----------------
    violations = []
    seen_ids = []
    # print(contract)
    table_contract = contract[0]
    print(table_contract)
    print("-----------------\n")
    table_name = table_contract.table_name

    # print(table_name)
    consumer_agent = table_contract.columns
    print(consumer_agent)
    print("-----------------\n")
    contract_columns = {column.column_name for column in table_contract.columns}
    column_contracts = {
        column.column_name: column for column in table_contract.columns}

    # print(contract_columns)
    print("--------------------")
    # print(column_contracts)
    print("TABLE:", table_name)
    print("CONTRACT COLUMNS:", contract_columns)
    print("INPUT ROW COUNT:", len(data))

    for row in data:
        print(row.keys())
    # return (violations)

def main():
    tee_stream = start_tee(__file__)
    print(f"script execution started {datetime.now().strftime('%Y-%m-%d-%Hh-%Mm-%Ss')}")

    check_validity_of_files(INCOMING_TRANSACTIONS_FILE)
    check_validity_of_files(CONTRACT_FILE)

    agnet_read_thru_contract = agent_readthru_contract(CONTRACT_FILE, Datacontract)
    # print(agnet_read_thru_contract)

    with open(INCOMING_TRANSACTIONS_FILE, "r") as file:
        incoming_data = json.load(file)
    all_violations = validate_data_against_contract(incoming_data, agnet_read_thru_contract)
    print(all_violations)
    print(f"script execution stopped@ {datetime.now().strftime("%Y-%m-%d")}")

    stop_tee(tee_stream)


if __name__ == "__main__":
    main()
