"""This system is build using pydntic, pdf, pdfplumber and gemini LLM
to scan the data from pdf and processit into structured json


Pipeline:
PDF → pdfplumber (text) → Gemini LLM (JSON) → Pydantic (validated)
"""

import os
import json
import pdfplumber
import config
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel, Field
from tee_logger import start_tee, stop_tee

CURR_DIR = Path(__file__).parent
PDF_FILE_NAME = "u7_loan_application_BFSI.pdf"
PDF_FILE_NAME_FULL_PATH = CURR_DIR.joinpath(PDF_FILE_NAME)
# print(PDF_FILE_NAME_FULL_PATH)
LOAN_APPL_PROCESSED = "u7_loan_applications.json"
LOAN_APPL_PROCESSED_PATH = CURR_DIR.joinpath(LOAN_APPL_PROCESSED)

client = OpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url=os.getenv("GEMINI_BASE_URL"))

model = os.getenv("GEMINI_MODEL_NAME")

class extracteddata(BaseModel):
    applicant_name:    str
    pan_number:        str
    aadhaar_number:    str
    mobile:            str
    email:             str
    employer_name:     str
    monthly_income:    float
    loan_amount:       float
    loan_tenure_years: int
    property_address:  str
    property_value:    float
    ltv_ratio:         float
    cibil_score:       int
    co_applicant:      str

PROMPT = f"""
You are a document extraction assistant for a bank.
Extract the following fields from the loan application text below.
Return ONLY a valid JSON object — no markdown, no backticks, no explanation.
If a field is not found, use "unknown" for strings and 0 for numbers.

Fields to extract:
- applicant_name (string)
- pan_number (string)
- aadhaar_number (string)
- mobile (string)
- email (string)
- employer_name (string)
- monthly_income (number — use net salary figure)
- loan_amount (number — remove INR and commas)
- loan_tenure_years (number)
- property_address (string)
- property_value (number — use market valuation figure)
- ltv_ratio (number — digits only, no % sign)
- cibil_score (number)
- co_applicant (string)

JSON OUTPUT:
"""

def extract_text_from_pdf(pdf_str: str) -> str:
    text = ""
    with pdfplumber.open(pdf_str) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
        # print(text)
    return text

def extract_fiields_with_llm(raw_text:str) -> dict:
    """raw text passed to Gemini LLM and fields extracted from text from extract_text_from_pdf"""
    # response = client.models.generate_content(
    #     model= model, contents=PROMPT,
    #     config={"response_mime_type": "application/json", "response_schema": extracteddata},
    # )
    response = client.chat.completions.parse(model=model, 
    messages= [
        {"role": "system",  "content": PROMPT},
        {"role": "user","content": f"Extract info from:\n\n{raw_text}"}
            ], response_format=extracteddata)
    
    data = response.choices[0].message.parsed
    # data = response.parsed
    # print(f"\nThe Extracted data is - \n {data}")
    data_dict = data.model_dump()
    return data.model_dump_json(indent = 4)

def already_processed(pan_number: str) -> bool:
    """check if this PAN already exists in the system"""
    if not LOAN_APPL_PROCESSED_PATH.exists():
        return False
    else:
        try:
            with open(LOAN_APPL_PROCESSED_PATH, "r") as file:
                existing_data = json.load(file)
            if existing_data.get("pan_number") == pan_number:
                print(f"\n[Cache] PAN {pan_number} - application already processed")
                return True
        except (json.JSONDecodeError, KeyError):
            return False
    # return True

def main():
    get_now = datetime.now()
    print('=' *60)
    print(f"Script Execution started at - {get_now}")
    tee_stream = start_tee(__file__)
    rawdata_from_pdf = extract_text_from_pdf(PDF_FILE_NAME_FULL_PATH)
    # want to check if same customer data already been processed or not 
    what_is_json_data = extract_fiields_with_llm(rawdata_from_pdf)
    data = json.loads(what_is_json_data)

    if already_processed(data["pan_number"]):
        print("\nalready processed - loading from cache")
        with open(LOAN_APPL_PROCESSED_PATH, "r") as file:
            print(json.dumps(json.load(file), indent = 4))
    else:
        print("\nNew application — saving...")
        with open(LOAN_APPL_PROCESSED_PATH, "w") as f:
            json.dump(data, f, indent=4)
            print(json.dump(data, f, indent=4))

    # print(what_is_json_data)

    get_now = datetime.now()
    print('=' *60)
    print(f"Script Execution Ended at - {get_now}")

    stop_tee(tee_stream)
if __name__ == "__main__":
    main()
    
