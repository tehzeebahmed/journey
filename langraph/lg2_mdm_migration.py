

import os
import json
from typing import TypedDict
from tee_logger import start_tee, stop_tee
from backupUtility import take_backup


#define class
class AgentState(TypedDict):
    record: dict
    errors: list[str]
    warnings: list[str]
    standardized: bool
    approved: bool

script_dir = os.path.dirname(os.path.abspath(__file__))
json_data_file = os.path.join(script_dir, 'lg2_agents_file.json')
#print (json_data_file)

take_backup(json_data_file)
def validation_agent(state: AgentState) -> AgentState:
    record = state["record"]
    required_fields = {
        "country_code", 
        "country_name",
        "currency",
        "status"
    }
    #check mandatory fields 
    for field in required_fields:
        if field not in record or record[field] =="":
            state["errors"].append(f" for {record.get('currency', 'unknown')} - {field} is missing")
            state["validation"] = False
            # break
        else:
            state["validation"] = True
    # print("Validtion complete ...")
        return state

def standardization_agent(state: AgentState) -> AgentState:
    record = state["record"]
    if "country_code" in record:
        record["country_code"] = record["country_code"].upper()
    if "country_name" in record:
        record["country_name"] = record["country_name"].upper()
    if record.get("currency") is None:
        state["errors"].append(f"currency is null for - {record.get('country_name', 'Unknown')}")
        record["status"]= "Error"
        state["standardized"] = False
    else:
            state["standardized"] = True
        # print(state)
    # print(state)
    return state
def report_agent(state:AgentState) -> AgentState:
    # print("\n========== Final Migration Report ==========")
    reportgeneration = []
    for key, value in state["record"].items():
        reportgeneration.append(f"{key:12} - {value}")
        # print(f" {key:35} - {value}")
    if state["errors"]:
        for error in state["errors"]:
            print("-", error)
    print("Standardized :", state["standardized"])
    print("error :", state["errors"])
    print("validation     :", state["validation"])
    # print(reportgeneration)
    return state

def main():    
    tee = start_tee(__file__)
    if os.path.exists(json_data_file):
        print(f" \n\n JSON Data file  exists .. going to do as planned \n")
        with open(json_data_file, "r") as file:
            records = json.load(file)
            # print(records)
            for index, record in enumerate(records):
                # print (f" {index} - {record.get("country_code")} ")
                state: AgentState = {
                    "record": record,
                    "errors": [],
                    "warnings": [],
                    "standardized": True,
                    "approved": True
                }
                # print(f" before {state}")
                state = validation_agent(state)
                state = standardization_agent(state)
                state = report_agent(state)
        with open(json_data_file, "w", encoding="UTF-8") as file:
            json.dump(records, file, indent=4, ensure_ascii=False)
        print(f"Successfully saved data in {json_data_file}")
    else:
        print(f"check the file - ")
    stop_tee(tee)
if __name__ == '__main__':
    main()
