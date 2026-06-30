"""
Module 1 — Concept 2 — Hands-on Task
Manual Tool Call Loop with Mistral (no frameworks)

What you will build:
  A bare tool-calling loop where YOU handle every step:
    1. Define a tool (get_employee_info)
    2. Send user question + tool definition to Mistral
    3. Detect that the model wants to call a tool
    4. Execute the tool yourself (local function)
    5. Inject the result back into the messages array
    6. Call the model again to get the final answer

Why this matters:
  Every agent framework (LangChain, LangGraph, CrewAI) does exactly
  this under the hood. Once you can build it manually, you understand
  what any framework is abstracting — and where it can go wrong.

Setup:
  pip install mistralai python-dotenv --break-system-packages
  MISTRAL_API_KEY in your .env
"""

import os
import json
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

MODEL = "mistral-small-latest"

# ── 1. Fake employee database (stands in for your JSON file / real DB) ─────────

EMPLOYEE_DB = {
    "pasha@company.com": {
        "name": "Pasha",
        "department": "Data Architecture",
        "salary": 140000,
        "city": "Toronto"
    },
    "alice@company.com": {
        "name": "Alice",
        "department": "Engineering",
        "salary": 120000,
        "city": "New York"
    }
}


# ── 2. The actual tool function — plain Python, nothing special ────────────────

def get_employee_info(email: str) -> dict:
    """Your real logic lives here. Could be a DB query, API call, file read."""
    record = EMPLOYEE_DB.get(email)
    if record:
        print(f"Employee found for email without tool calling: {email} → {record}")
        return {"found": True, "employee": record}
    print(f"Employee not found for email: {email}")
    return {"found": False, "message": f"No employee found for {email}"}


# ── 3. Tool definition — what you send to the model so it knows what exists ───
# This is JSON Schema. The model reads this and decides if/when to call the tool.

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_employee_info",
            "description": (
                "Look up an employee record by their email address. "
                "Returns name, department, salary, and city."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "The employee's email address"
                    }
                },
                "required": ["email"]
            }
        }
    }
]


# ── 4. Tool executor — routes model requests to real functions ─────────────────
# In a real agent you'd have many tools here. This is the dispatcher.

def execute_tool(tool_name: str, arguments: dict) -> str:
    """
    The model tells you WHAT to run and with WHAT arguments.
    You decide HOW to run it and return the result as a string.
    """
    if tool_name == "get_employee_info":
        result = get_employee_info(**arguments)
        return json.dumps(result)
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ── 5. The manual agent loop ───────────────────────────────────────────────────

def run_agent(user_question: str) -> str:
    """
    The full tool-calling loop — every step explicit, nothing hidden.

    Step 1: Send question + tool definitions → model decides what to do
    Step 2: If model calls a tool → execute it, inject result, call again
    Step 3: If model replies directly → return the answer

    This loop can repeat if the model makes multiple tool calls.
    That's exactly what a ReAct agent does — it just automates this.
    """
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

    messages = [
        {"role": "user", "content": user_question}
    ]

    print(f"\n{'─'*60}")
    print(f"USER: {user_question}")
    print(f"{'─'*60}")

    # Loop: keep going until the model gives a final text answer
    step = 0
    while True:
        step += 1
        print(f"\n[Step {step}] Calling Mistral...")

        response = client.chat.complete(
            model=MODEL,
            temperature=0,
            tools=TOOLS,
            messages=messages
        )

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        print(f"[Step {step}] Finish reason: {finish_reason}")

        # ── Case A: model wants to call a tool ────────────────────────────────
        if finish_reason == "tool_calls":
            # Append the model's tool request to message history
            messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Execute each tool call and inject results
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                print(f"[Step {step}] Model requested tool: {tool_name}")
                print(f"[Step {step}] Arguments: {arguments}")

                # *** YOUR CODE runs the tool — not the model ***
                result = execute_tool(tool_name, arguments)

                print(f"[Step {step}] Tool result: {result}")

                # Inject result back into messages so model can see it
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

        # ── Case B: model has a final answer ─────────────────────────────────
        elif finish_reason == "stop":
            final_answer = message.content
            print(f"\n{'─'*60}")
            print(f"AGENT: {final_answer}")
            print(f"{'─'*60}")
            print(f"\nTotal steps: {step} | Total messages in context: {len(messages)}")
            return final_answer

        else:
            print(f"Unexpected finish reason: {finish_reason}")
            break


# ── 6. Main — try a few different questions ────────────────────────────────────

if __name__ == "__main__":
    if not os.getenv("MISTRAL_API_KEY"):
        raise ValueError("MISTRAL_API_KEY not found in .env")

    # Question 1: model needs to call the tool
    run_agent("What department does pasha@company.com work in?")

    # Question 2: employee not in DB — observe how the model handles it
    run_agent("Can you find details for bob@company.com?")

    # Question 3: no tool needed — model answers from general knowledge
    # Watch: finish_reason goes straight to "stop", no tool call happens
    run_agent("What is the capital of France?")

    # ── SELF-CHECK QUESTIONS ──────────────────────────────────────────────────
    # After running, answer these to verify your understanding:
    #
    # Q1: In Question 1, how many total API calls were made to Mistral?
    #     (hint: count the while loop iterations in the printed steps)
    #
    # Q2: What is in messages[] just before the second Mistral call?
    #     Draw it out: [user msg, assistant tool_call msg, tool result msg]
    #
    # Q3: In Question 3, why does the loop exit in step 1 with no tool call?
    #
    # Q4: What would happen if execute_tool() raised an exception?
    #     How would you handle that in a production agent?
    #
    # Q5: The model returns arguments as a JSON STRING, not a dict.
    #     Find the line where we parse it. What breaks if we skip that?