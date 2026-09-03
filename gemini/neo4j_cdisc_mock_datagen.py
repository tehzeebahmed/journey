import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

PATH = Path(__file__).parent
TERGET_PARAM_FILE = PATH.joinpath("neo4j_cdisc_mock_records.json")

# Core parameter structure configuration
params = { 
    "study_params": {"id": "NN-DIABETES-001", "title": "Type 2 Diabetes Evaluation", "phase": "Phase III"}, 
    "visit_params": {"id": "V-WEEK-04", "name": "Week 4 Follow-up", "week": 4}, 
    "element_params": {"id": "DE-SYS-BP", "label": "Systolic Blood Pressure", "variable": "BPSYS"}, 
    "term_params": {"code": "271649006", "name": "Systolic blood pressure (observable entity)", "system": "SNOMED-CT"} 
}

def generate_nested_json_records(num_records=10000):
    # Fixed seed for consistent mock statistical values
    np.random.seed(42)
    
    # Generate clinical values for Systolic Blood Pressure (Normal distribution)
    sbp_values = np.random.normal(loc=132, scale=14, size=num_records).round(0).astype(int)
    
    records = []
    for i in range(num_records):
        # Create an object matching the exact nested formatting
        record = {
            "study_params": params["study_params"].copy(),
            "visit_params": params["visit_params"].copy(),
            "element_params": params["element_params"].copy(),
            "term_params": params["term_params"].copy(),
            "subject_data": {
                "usubjid": f"SUBJ-{i+1:05d}",
                "value": int(sbp_values[i]),
                "unit": "mmHg"
            }
        }
        records.append(record)
        
    return records

if __name__ == "__main__":
    json_dataset = generate_nested_json_records(10000)
    
    # Exporting directly to JSON format
    with open(TERGET_PARAM_FILE, "w") as json_file:
        json.dump(json_dataset, json_file, indent=2)
        
    print(f"Successfully generated {len(json_dataset)} structured JSON objects.")
