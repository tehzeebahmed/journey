"""
Module 1 — Concept 1 — Task 3
Temperature vs Determinism

What you will see:
  temperature=0.0 — same prompt x3 → nearly identical output every time
  temperature=1.2 — same prompt x3 → noticeably different output every time

Why it matters for agents:
  Tool calls, JSON extraction, SQL generation → always temperature=0
  Creative tasks, brainstorming, content gen  → temperature > 0 acceptable

Setup:
  pip install mistralai python-dotenv --break-system-packages
  MISTRAL_API_KEY in your .env
"""

import os
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

MODEL  = "mistral-small-latest"
RUNS   = 3
PROMPT = (
    "In one sentence, name the single most important design decision "
    "when building a multi-agent AI system."
)

def call(client: Mistral, temperature: float) -> str:
    r = client.chat.complete(
        model=MODEL,
        temperature=temperature,
        max_tokens=60,
        messages=[{"role": "user", "content": PROMPT}]
    )
    return r.choices[0].message.content.strip()

def run_experiment(client: Mistral, temperature: float):
    label = f"temperature={temperature}"
    sep   = "─" * 60
    print(f"\n{sep}")
    print(f"  {label}  —  {RUNS} runs, same prompt")
    print(sep)
    outputs = []
    for i in range(1, RUNS + 1):
        answer = call(client, temperature)
        outputs.append(answer)
        print(f"  Run {i}: {answer}")

    # simple variance check: are all outputs identical?
    unique = set(outputs)
    print(f"\n  Unique responses : {len(unique)} of {RUNS}")
    print(f"  Verdict          : {'DETERMINISTIC ✓' if len(unique) == 1 else 'VARIABLE — outputs differ'}")
    print(sep)

def main():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in .env")

    client = Mistral(api_key=api_key)

    print(f"\nPrompt: \"{PROMPT}\"")

    run_experiment(client, temperature=0.0)
    run_experiment(client, temperature=1.2)

    print("""
ARCHITECT TAKEAWAY
─────────────────────────────────────────────────────────
temperature=0   → near-deterministic. Use for ALL agent
                  tool calls, JSON output, SQL, decisions.

temperature>0   → variable. Use only when variety is the
                  goal (creative writing, brainstorming).

Rule of thumb   → if a downstream system parses the output,
                  temperature must be 0. No exceptions.
─────────────────────────────────────────────────────────
""")

if __name__ == "__main__":
    main()