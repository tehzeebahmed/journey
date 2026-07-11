"""
this code is understanding langchain, langrpah and tool calling
"""

import os
from datetime import datetime 
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from tee_logger import start_tee, stop_tee


client = OpenAI(api_key=os.getenv("MISTRAL_API_KEY"), base_url=os.getenv("MISTRAL_BASE_URL"))
curr_file_path = os.path.abspath(__file__)
target_jason_file, extn = os.path.splitext(curr_file_path)
target_jason_file = target_jason_file + '.json'
# print(f"{curr_file_path} - {target_jason_file}")
class countryrecordClass(BaseModel):
    country_code: str  = Field(description= "Standard Country Code")
    country_name: str = Field(description="Country Name in full")
    currency:     str = Field(description="Currency code for the country")
    status:       str = Field(description="state of the record if validated and approved")

def create_reord(
        ccode: str, 
        cname: str,
        curr: str,
        state: str
):
    print(f"entering data for country - {cname}")
    country_data = {
        "country_code": ccode,
        "country_name": cname,
        "currency":     curr,
        "status":       state
    }
    if os.path.exists(target_jason_file):
        with open(target_jason_file, 'r') as file:
            country_record = json.load(file)
            # not check if country already exists
            existing_record = next((record for record in country_record
                                   if record['country_code'] == ccode), None)
            if existing_record:
                print (f" Record Exists for {ccode}")
            else:
                country_record.append(country_data)
                with open (target_jason_file, "w") as file:
                    json.dump(country_record,file, indent=4)
                    print(f" Country record for {ccode} - added to database")
    else:
        country_record = []
        country_record = [country_data]
        with open(target_jason_file, "w") as file:
            json.dump(country_record, file, indent = 4)
            print(f"Database initialized. Country record for {ccode} added.")


    return {
         "status": "success",
         "message": "Country record created",
         "record": country_data
         }
def main():
    print("\n\n specify the details you want to insert")
    country_code = input(" Country Code :")
    country_name = input(" Country Name : ")
    country_curr = input(" Country currency :")
    state = "Initialized"
    result = create_reord(country_code, country_name, country_curr, state)
    print(result)

if __name__ == '__main__':
    main()
    
