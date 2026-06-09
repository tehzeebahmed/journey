"""
Module 1 — Concept 1 — Task 2
Proving LLM Statelessness with Mistral AI

What you will see:
  Call 1 — follow-up question sent WITHOUT history  → model is confused
  Call 2 — follow-up question sent WITH history     → model answers correctly

Same model. Same follow-up question. Completely different result.
This is the most important thing to internalize before building any agent.

Setup:
  pip install mistralai python-dotenv --break-system-packages
  Add MISTRAL_API_KEY=your_key to your .env file
  Get a free key at: https://console.mistral.ai
"""

import os
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

MODEL = "mistral-small-latest"   # free tier, fast, sufficient for this exercise

# ── Messages ──────────────────────────────────────────────────────────────────

# Turn 1 — the opening question (same for both calls)
TURN_1_USER = "What are the three main types of memory in an agentic AI system?"

# Simulated assistant reply to turn 1 (we use this to inject history in call 2)
TURN_1_ASSISTANT = (
    "The three main types of memory in an agentic AI system are: "
    "1) In-context memory — text inside the active context window. "
    "2) External memory — vector stores or databases retrieved via search. "
    "3) In-weights memory — knowledge baked into the model during training."
)

# Turn 2 — the follow-up (sent in BOTH calls, but only call 2 has the history)
TURN_2_USER = "Which of those three is the most expensive to scale, and why?"


# ── API call helper ───────────────────────────────────────────────────────────

def call_mistral(client: Mistral, messages: list[dict]) -> str:
    response = client.chat.complete(
        model=MODEL,
        temperature=0,
        messages=messages
    )
    return response.choices[0].message.content


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in .env")

    client = Mistral(api_key=api_key)

    separator = "─" * 60

    # ── Call 1: NO history — model has no idea what "those three" refers to ──
    print(separator)
    print("CALL 1 — follow-up sent WITHOUT conversation history")
    print(separator)

    messages_without_history = [
        {"role": "user", "content": TURN_2_USER}   # jumps straight to follow-up
    ]

    print(f"Messages sent : {len(messages_without_history)} turn(s)")
    print(f"Question      : {TURN_2_USER}\n")

    answer_1 = call_mistral(client, messages_without_history)
    print(f"Model response:\n{answer_1}")

    # ── Call 2: WITH history — model has full context ─────────────────────────
    print(f"\n{separator}")
    print("CALL 2 — follow-up sent WITH conversation history injected")
    print(separator)

    messages_with_history = [
        {"role": "user",      "content": TURN_1_USER},        # original question
        {"role": "assistant", "content": TURN_1_ASSISTANT},   # prior answer
        {"role": "user",      "content": TURN_2_USER}         # follow-up
    ]

    print(f"Messages sent : {len(messages_with_history)} turn(s)")
    print(f"Question      : {TURN_2_USER}\n")

    answer_2 = call_mistral(client, messages_with_history)
    print(f"Model response:\n{answer_2}")

    # ── Architect's takeaway ──────────────────────────────────────────────────
    print(f"\n{separator}")
    print("ARCHITECT TAKEAWAY")
    print(separator)
    print("The model has zero memory between calls.")
    print("'Memory' in an agent is YOUR code — not the model.")
    print("You decide what history to keep, compress, or discard.")
    print("Every token of history you carry = cost on every subsequent call.")
    print(separator)


if __name__ == "__main__":
    main()