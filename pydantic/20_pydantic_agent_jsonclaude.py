"""
Employee Record Manager
-----------------------
Creates or updates employee records in a JSON file.
Uses: Pydantic validation, Gemini LLM, LangGraph ReAct agent, JSON storage.

FIX SUMMARY (vs original):
  1.  Removed duplicate `import email` (unused) — use EmailStr from pydantic instead.
  2.  Added `load_dotenv()` so your .env file is actually read.
  3.  Switched model to "gemini-2.0-flash" — more generous free-tier quota than 2.5-flash.
      If you still hit 429, switch to "gemini-1.5-flash" which has the highest free quota.
  4.  Fixed import: `create_react_agent` from langgraph (langchain has no `create_agent`).
  5.  Fixed `get_next_employee_id`: removed broken `.replace("","")` — use int() directly.
  6.  Simplified `create_or_update_employee`: removed nested file open inside read block
      (inner write was redundant and confusing); now one clean read → modify → write flow.
  7.  Fixed return message to correctly say "updated" vs "created".
  8.  Added try/except inside the tool so tool errors are caught and logged properly.
  9.  Added logging for the final write in both update and create paths.
  10. Consistent indentation (mixed tabs/spaces fixed throughout).
"""

import os
import json
import logging
from datetime import datetime

from dotenv import load_dotenv                          # FIX 2: actually loads .env
from pydantic import BaseModel, Field, EmailStr
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent      # FIX 4: correct import
from langchain_core import tools

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler("20_pydantic_agent_json2.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

RECORDS_FILE = "20_employee_records.json"


# ── LLM factory ──────────────────────────────────────────────────────────────
def create_gemini_llm() -> ChatGoogleGenerativeAI:
    load_dotenv()                                       # FIX 2: load .env first
    logger.info("Reading GEMINI_API_KEY from environment...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        msg = "GEMINI_API_KEY not found. Set it in your .env or environment."
        logger.error(msg)
        raise ValueError(msg)

    logger.info("GEMINI_API_KEY found. Creating Gemini LLM...")
    # FIX 3: gemini-2.0-flash has a higher free-tier quota than gemini-2.5-flash.
    # Free tier limits (as of 2025): 2.0-flash = 1500 req/day; 2.5-flash = 20 req/day.
    # Swap to "gemini-1.5-flash" if you still hit quota limits.
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    logger.info("Gemini LLM created successfully.")
    return llm


# ── Pydantic schema ───────────────────────────────────────────────────────────
class EmployeeRecord(BaseModel):
    name:       str      = Field(description="Full name of the employee")
    city:       str      = Field(description="City where the employee resides")
    age:        int      = Field(ge=18, le=65, description="Age (18–65)")
    salary:     int      = Field(ge=0,         description="Salary (non-negative)")
    department: str      = Field(description="Department of the employee")
    email:      EmailStr = Field(description="Valid email address of the employee")
    country:    str      = Field(description="Country where the employee resides")


# ── Helper: next employee ID ──────────────────────────────────────────────────
def get_next_employee_id(email_in: str) -> str:
    """
    Returns the existing employee_id if the email already exists,
    otherwise generates the next sequential ID (EMP0001, EMP0002, …).
    Also ensures the records file exists.
    """
    if not os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "w") as f:
            json.dump([], f)
        logger.info(f"Created new records file: {RECORDS_FILE}")

    with open(RECORDS_FILE, "r") as f:
        records: list[dict] = json.load(f) # explaination: list[dict] is a type hint indicating that records is expected to be a list of dictionaries. This helps with code readability and can assist IDEs in providing better autocompletion and error checking.

    if records:
        # Check if employee already exists by email
        existing = next((r for r in records if r["email"] == email_in), None)
        if existing:
            logger.info(
                f"Email {email_in} found — reusing ID {existing['employee_id']}"
            )
            return existing["employee_id"]

        # FIX 5: removed broken .replace("","") — just strip "EMP" then cast to int
        last_num = int(records[-1]["employee_id"].replace("EMP", ""))
        next_id = f"EMP{str(last_num + 1).zfill(4)}"
        logger.info(f"New employee — assigned ID {next_id}")
        return next_id

    logger.info("No records yet — assigning EMP0001")
    return "EMP0001"


# ── Tool definition ───────────────────────────────────────────────────────────
@tools.tool(args_schema=EmployeeRecord)
def create_or_update_employee(
    name: str,
    city: str,
    age: int,
    salary: int,
    department: str,
    email: EmailStr,
    country: str,
) -> dict:
    """
    Create or update an employee record in the JSON file.
    If an employee with the same email already exists the record is updated;
    otherwise a new record is inserted with the next sequential ID.
    """
    logger.info("======== TOOL USAGE: create_or_update_employee ========")

    # FIX 8: wrap entire tool body in try/except so errors surface cleanly
    try:
        employee_id = get_next_employee_id(email_in=email)

        employee_data = {
            "employee_id": employee_id,
            "name":        name,
            "city":        city,
            "age":         age,
            "salary":      salary,
            "department":  department,
            "email":       email,
            "country":     country,
            "timestamp":   datetime.now().isoformat(),
        }

        # FIX 6: one clean read → modify → write (no nested open inside read block)
        if os.path.exists(RECORDS_FILE):
            with open(RECORDS_FILE, "r") as f:
                records: list[dict] = json.load(f)
        else:
            records = []

        existing_idx = next(
            (i for i, r in enumerate(records) if r["employee_id"] == employee_id),
            None,
        )

        if existing_idx is not None:
            records[existing_idx] = employee_data          # replace in-place
            action = "updated"
            logger.info(f"Employee {employee_id} ({name}) updated.")
        else:
            records.append(employee_data)                  # append new
            action = "created"
            logger.info(f"Employee {employee_id} ({name}) created.")

        # FIX 9: single final write with logging for both paths
        with open(RECORDS_FILE, "w") as f:
            json.dump(records, f, indent=4)
        logger.info(f"Records file written successfully after {action}.")

        # FIX 7: return message now correctly reflects action taken
        return {
            "status":  "success",
            "message": f"Employee record {action} successfully.",
            "record":  employee_data,
        }

    except Exception as exc:
        logger.error(f"Tool error in create_or_update_employee: {exc}", exc_info=True)
        return {"status": "error", "message": str(exc)}


# ── Agent factory ─────────────────────────────────────────────────────────────
def main():
    logger.info("=== Starting employee record agent ===")
    try:
        llm = create_gemini_llm()
    except Exception as e:
        logger.error(f"Failed to create LLM: {e}")
        raise

    logger.info("Building ReAct agent with create_or_update_employee tool...")
    # FIX 4: create_react_agent is the correct LangGraph API
    agent = create_react_agent(model=llm, tools=[create_or_update_employee])
    logger.info("Agent ready.")
    return agent


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    agent = main()

    logger.info("Waiting for user input...")
    print("\nEmployee Record Agent — type your request below.")
    print('Example: "Create a record for John Doe, age 30, Engineer in NYC, USA, salary 90000, john@example.com"')
    question = input("\nYour request for llm: ").strip()

    if not question:
        print("No input provided. Exiting.")
    else:
        logger.info(f"Invoking agent with: {question}")
        try:
            answer = agent.invoke(
                {"messages": [{"role": "user", "content": question}]}
            )
            final_answer = answer["messages"][-1].content
            logger.info(f"Agent final answer: {final_answer}")
            print(f"\nAgent response: {final_answer}")
        except Exception as e:
            logger.error(f"Agent invocation error: {e}", exc_info=True)
            print(f"Error: {e}")
