"""
Data contract Schema
it validates a schema changes overtime(versioning of the schema changes)
"""
import config
import json
import sys
import time
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pathlib import Path
from tee_logger import start_tee, stop_tee
from llm_router import chat

CURR_PATH = Path(__file__).parent
INCOMING_TRANSACTIONS_FILE = CURR_PATH.joinpath("gm1_incoming_transactions.json")
CONTRACT_FILE = CURR_PATH.joinpath("gm1_contract.json")
VERSION_FILE = CURR_PATH.joinpath("gm1_clmn_violation_version.json")
PROMPT = """You are a helpful assitant and you alert that with data contract validation failure there 
will ne autosys job p_load_silver_transactions will be failed at its scheduled time
the input you have in this format

severity:
violation_type:
version:
column name: 
value/error:
Generate the email alert in full. Do not truncate, summarize, or leave placeholders open. Ensure you write out the message completely from the subject line to the signature block.
"""
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
    version: int  = 1      # to keep counts how many times this columns has ciolations
    affected_rows: int        # Total no if rows affected
    sample_values: str        # values from incoming record
    severity: str              # Critical/Warning 
    detected_at: str           # Time stamp
    consumer_agents: list[str] # which agent is impacted
    impact_date: str = datetime.now().isoformat()

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
    table_name = table_contract.table_name
    # print(table_contract.columns)
    # print(";;;;;;;;;;;;;;;;;;;;;;;")
    # print(table_name)
    consumer_agent = table_contract.consumer_agents
    col_names_in_datacontract = {column.column_name for column in table_contract.columns}
    full_column_further_details = {column.column_name for column in table_contract.columns}

    print(full_column_further_details)
    print("--------------------")
    # print(column_contracts)
    print("TABLE:", table_name)
    print("CONTRACT COLUMNS:", col_names_in_datacontract)
    # print("Full column details:", full_column_further_details)
    print("INPUT ROW COUNT:", len(data))

    with open(VERSION_FILE, "r") as read_versions:
         all_versions = json.load(read_versions)
    version_lookup = {(r["column_name"], r["violation_type"]): r["version"]  for r in all_versions}
    # print(f"lookup --------{all_versions}")
    for row in data:
        # print(f"\nrow\n")
        # print("\n -=-=-=-0=-=-=-0=-=-=-=-=-=-=-=")
        # print(f"Key - {row.keys()}, table_name- {table_name}, column_name-{row.keys()}")
        trxn_id = row.get("transaction_id")
        if trxn_id in seen_ids:
            key = ("transaction_id", "duplicate_record")
            # print(f"kkkkey ----- {key}")
            version = version_lookup.get(key, 0) + 1
            # print(f"\n the versions value - {version}")
            violations.append(contractViolation
                              (table_name      = table_name,
                               column_name     = "transaction_id", 
                               violation_type  = "duplicate_record",
                               version         =  version,
                               affected_rows   = 1,
                               sample_values   = str(trxn_id),
                               severity        = "critical",
                               detected_at     = datetime.now().isoformat(),
                               consumer_agents = consumer_agent))
        else:
            seen_ids.append(trxn_id)
        # print(violations)
        # New CoLlumn 
        # --------------
        for key in row.keys():
            if key not in col_names_in_datacontract:
                key1 = (key, "new_column")
                version = version_lookup.get(key1, 0) + 1
                violations.append(contractViolation
                              (table_name      = table_name,
                               column_name     = key,
                               violation_type  = "new_column",
                               version         =  version,
                               affected_rows   = 1,
                               sample_values   = str(row.get(key)),
                               severity        = "Warning",
                               detected_at     = datetime.now().isoformat(),
                               consumer_agents = consumer_agent))
        for col in table_contract.columns:
            value = row.get(col.column_name)
            # print(f"\nRequired of col -{col}.{col.required} - value {value}")
            if col.required and value is None:
                # key = (f"'column_name': '{col.column_name}', 'violation_type': {"'null_value'"}")
                key = (col.column_name, "null_value")
                # print(f"key -----------{key}")
                version = version_lookup.get(key, 0) + 1
                # print(f"version ---------------{version_lookup.get(key)}")
                violations.append(contractViolation
                              (table_name      = table_name,
                               column_name     = col.column_name,
                               violation_type  = "null_value",
                               version         =  version,
                               affected_rows   = 1,
                               sample_values   = "None",
                               severity        = "Warning",
                               detected_at     = datetime.now().isoformat(),
                               consumer_agents = consumer_agent))
            if col.allowed_values is not None and value is not None and value not in col.allowed_values:
                key = (col.column_name, "invalid_enum")
                version = version_lookup.get(key, 0) + 1
                violations.append(contractViolation
                              (table_name      = table_name,
                               column_name     = col.column_name,
                               violation_type  = "invalid_enum",
                               version         =  version,
                               affected_rows   = 1,
                               sample_values   = str(value),
                               severity        = "Warning",
                               detected_at     = datetime.now().isoformat(),
                               consumer_agents = consumer_agent))
            if col.min_value  is not None and value is not None and value < col.min_value:
                key = (col.column_name, "out_of_range")
                version = version_lookup.get(key, 0) + 1
                violations.append(contractViolation
                              (table_name      = table_name,
                               column_name     = col.column_name,
                               violation_type  = "out_of_range",
                               version         =  version,
                               affected_rows   = 1,
                               sample_values   = "None",
                               severity        = "Critical",
                               detected_at     = datetime.now().isoformat(),
                               consumer_agents = consumer_agent))

    return (violations)

def generate_alert(violations: contractViolation) -> str:
    """this generates the output into human language"""
    prompt_data = f"""
    Severity:       {violations.severity}
    violation_type: {violations.violation_type}
    Version:        {violations.version}
    Column Name:    {violations.column_name}
    Value/error:    {violations.sample_values}
    Consumer agents impacted: {''.join(violations.consumer_agents)}
"""
    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": prompt_data}
    ]
    print(chat(messages))

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
    json_ready_data = [v.__dict__ for v in all_violations]
    updated_versions = []
    for v in all_violations:
        updated_versions.append({
            "column_name": v.column_name,
            "violation_type": v.violation_type,
            "version": v.version,
            "last_seen": v.detected_at
        })
    with open(VERSION_FILE, "w") as version_write_file:
         json.dump(updated_versions, version_write_file, indent = 4)
    # print(all_violations)
    print(f"\nTotal violations found: {len(all_violations)}")
    # sys.stdout.flush()
    for v in all_violations:
        time.sleep(1) 
        print(f"{v.severity.upper():9} | {v.violation_type:<16} | version no - {v.version:3} | column_name-{v.column_name:16} | value - {v.sample_values}")
        #  violation_for_llm = f"{v.severity.upper():9} | {v.violation_type:<16} | version no - {v.version:3} | column_name-{v.column_name:16} | value - {v.sample_values}"
        generate_alert(v)    

    # print(f"script execution stopped@ {datetime.now().strftime("%Y-%m-%d")}")
    stop_tee(tee_stream)


if __name__ == "__main__":
    main()
