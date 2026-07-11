"""
Module 2 — Concept 2
Employee record agent rebuilt as an explicit LangGraph StateGraph.

WHAT THIS SCRIPT TEACHES:
  - State flows through every node as a typed dict
  - Node 1 (llm_node)  : LLM reads messages, decides to call a tool or answer
  - Node 2 (tool_node) : YOUR CODE executes the tool, writes result to state
  - Conditional edge   : routes to tool_node or END based on LLM output
  - The LLM never executes the tool — it only requests it

THE GRAPH:
  START → llm_node → [conditional edge] → tool_node → llm_node (loop)
                                        ↘ END
"""

import os
import json
from datetime import datetime
import logging
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langchain_mistralai import ChatMistralAI
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('lg1_nodes_tool_call.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

RECORDS_FILE = "employee_records.json"
SALARY_REVIEW_THRESHOLD = 200_000


# ── State ──────────────────────────────────────────────────────────────────────
# This dict is the agent's working memory.
# Every node receives it, modifies it, and returns it.

class AgentState(TypedDict):
    messages:              Annotated[list, add_messages]  # full conversation history
    employee_email:        str    # set by tool_node after tool runs
    requires_human_review: bool   # True if salary > 200,000
    action_taken:          str    # "created" or "updated"


# ── Pydantic schema ────────────────────────────────────────────────────────────

class EmployeeRecord(BaseModel):
    name:        str      = Field(description="Full name")
    age:         int      = Field(ge=18, le=65, description="Age 18-65")
    department:  str      = Field(description="Department")
    designation: str      = Field(description="Job title / designation")
    salary:      float    = Field(ge=0, description="Annual salary")
    email:       EmailStr = Field(description="Work email address")
    country:     str      = Field(description="Country of residence")


# ── Helper — plain Python function, no @tool decorator ────────────────────────

def get_next_employee_id(email_in: str) -> str:
    """Returns existing employee_id for email, or generates the next one."""
    if not os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "w") as f:
            json.dump([], f)
    with open(RECORDS_FILE, "r") as f:
        records = json.load(f)
    if records:
        existing = next((r for r in records if r["email"] == email_in), None)
        if existing:
            logger.info("Existing employee found: %s", existing["employee_id"])
            return existing["employee_id"]
        last_num = int(records[-1]["employee_id"].replace("EMP", ""))
        return f"EMP{str(last_num + 1).zfill(4)}"
    return "EMP0001"


# ── Tool — @tool decorator lives HERE ─────────────────────────────────────────
# The LLM sees this tool definition and decides when to call it.
# YOUR CODE (tool_node) is what actually runs it.

@tool(args_schema=EmployeeRecord)
def create_or_update_employee(
    name: str, age: int, department: str,
    designation: str, salary: float,
    email: EmailStr, country: str
) -> dict:
    """Create or update an employee record in the JSON file."""
    logger.info("Tool executing: create_or_update_employee for %s", email)
    try:
        employee_id = get_next_employee_id(email_in=email)
        employee_data = {
            "employee_id": employee_id,
            "name":        name,
            "age":         age,
            "department":  department,
            "designation": designation,
            "salary":      salary,
            "email":       email,
            "country":     country,
            "timestamp":   datetime.now().isoformat(),
        }

        records = []
        if os.path.exists(RECORDS_FILE):
            with open(RECORDS_FILE, "r") as f:
                records = json.load(f)

        existing_idx = next(
            (i for i, r in enumerate(records) if r["employee_id"] == employee_id),
            None
        )

        if existing_idx is not None:
            records[existing_idx] = employee_data
            action = "updated"
        else:
            records.append(employee_data)
            action = "created"

        with open(RECORDS_FILE, "w") as f:
            json.dump(records, f, indent=4)

        logger.info("Employee %s %s", employee_id, action)
        return {
            "status":  "success",
            "message": f"Employee record {action} successfully.",
            "record":  employee_data
        }

    except Exception as e:
        logger.error("Tool error: %s", e, exc_info=True)
        return {"status": "error", "message": str(e)}


# ── Node 1: LLM ───────────────────────────────────────────────────────────────
# Reads state["messages"], calls the LLM, returns updated messages.
# The LLM either returns a tool_call request OR a final text answer.
# This node does NOT execute the tool — it only asks for it.

def llm_node(state: AgentState) -> dict:
    """Call the LLM. It decides: request a tool call, or give a final answer."""
    llm = ChatMistralAI(model="mistral-small-latest", temperature=0)
    llm_with_tools = llm.bind_tools([create_or_update_employee])

    logger.info("llm_node: calling LLM with %d messages", len(state["messages"]))
    response = llm_with_tools.invoke(state["messages"])
    logger.info("llm_node: LLM responded — tool_calls=%s", bool(response.tool_calls))

    return {"messages": [response]}


# ── Node 2: Tool execution ─────────────────────────────────────────────────────
# The LLM requested a tool. This node:
#   1. Reads the tool name + arguments from the last message
#   2. Executes the actual Python function
#   3. Writes the result + metadata back into state
# The LLM is idle during this entire node.

def tool_node(state: AgentState) -> dict:
    """Execute the tool the LLM requested. Write result to state."""
    last_message = state["messages"][-1]
    tool_call    = last_message.tool_calls[0]
    tool_args    = tool_call["args"]

    logger.info("tool_node: executing tool '%s' with args: %s", tool_call["name"], tool_args)

    # Step 1 — run the tool function
    result = create_or_update_employee.invoke(tool_args)

    # Step 2 — extract email from the arguments the LLM provided
    employee_email = tool_args.get("email", "")

    # Step 3 — flag for human review if salary exceeds threshold
    requires_human_review = tool_args.get("salary", 0) > SALARY_REVIEW_THRESHOLD

    # Step 4 — extract what action the tool took ("created" or "updated")
    action_taken = "updated" if "updated" in result.get("message", "") else "created"

    logger.info(
        "tool_node: email=%s action=%s hitl=%s",
        employee_email, action_taken, requires_human_review
    )

    # Step 5 — return updated state
    # ToolMessage carries the tool result back to the LLM on the next loop iteration
    return {
        "messages": [
            ToolMessage(
                content=json.dumps(result),
                tool_call_id=tool_call["id"]
            )
        ],
        "employee_email":        employee_email,
        "requires_human_review": requires_human_review,
        "action_taken":          action_taken,
    }


# ── Conditional edge ───────────────────────────────────────────────────────────
# Called after llm_node. Inspects the last message.
# If the LLM made a tool call → route to tool_node
# If the LLM gave a final answer → route to END

def should_call_tool(state: AgentState) -> str:
    """Route: 'tool' if LLM called a tool, 'end' if LLM gave a final answer."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        logger.info("Routing → tool_node")
        return "tool"
    logger.info("Routing → END")
    return "end"


# ── Build the graph ────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("llm",   llm_node)
    graph.add_node("tools", tool_node)

    # Fixed edge: always start at llm_node
    graph.add_edge(START, "llm")

    # Conditional edge: after llm_node, inspect state and route
    graph.add_conditional_edges(
        "llm",
        should_call_tool,
        {"tool": "tools", "end": END}
    )

    # Fixed edge: after tool_node, always return to llm_node
    graph.add_edge("tools", "llm")

    return graph.compile()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    graph = build_graph()

    print("\n" + "="*60)
    print("  Employee Agent — LangGraph (explicit StateGraph)")
    print("="*60)
    print("Example: 'Create a record for Sara Ali, age 32,")
    print("  Engineering, Senior Engineer, salary 95000,")
    print("  sara@company.com, UAE'")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("Your request: ").strip()
        if not user_input or user_input.lower() in {"exit", "quit"}:
            print("Exiting.")
            break

        initial_state = {
            "messages":              [{"role": "user", "content": user_input}],
            "employee_email":        "",
            "requires_human_review": False,
            "action_taken":          ""
        }

        logger.info("Invoking graph with: %s", user_input)
        result = graph.invoke(initial_state)

        print("\n" + "-"*60)
        print("Agent      :", result["messages"][-1].content)
        print("Action     :", result["action_taken"])
        print("Email      :", result["employee_email"])
        print("HITL flag  :", result["requires_human_review"])
        if result["requires_human_review"]:
            print("⚠️  Salary exceeds threshold — requires manager approval")
        print("-"*60 + "\n")


if __name__ == "__main__":
    main()