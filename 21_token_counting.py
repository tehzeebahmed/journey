"""
Module 1 — Concept 1 — Task 1
Bare API call + token counting + cost estimation

What you will learn:
  - How to call Mistral directly (no LangChain, no agent framework)
  - How to estimate tokens BEFORE sending (pre-flight budget check)
  - How system prompt + user message + response all draw from one budget
  - How to estimate cost per call — essential for agent cost control

Install:
  pip install mistralai python-dotenv "mistral-common[sentencepiece,hf-hub]"
  MISTRAL_API_KEY=your_key python 21_token_counting.py
"""

import os
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

# ── 1. Constants ───────────────────────────────────────────────────────────────
MODEL = "mistral-large-latest"

# Mistral pricing (as of 2025 — always check mistral.ai for updates)
# Input:  $2.00 per 1M tokens  (mistral-large-latest)
# Output: $6.00 per 1M tokens
# https://mistral.ai/technology/#pricing
COST_PER_1M_INPUT  = 2.00
COST_PER_1M_OUTPUT = 6.00


# ── 2. Build your messages ─────────────────────────────────────────────────────
# This is the EXACT structure every LLM API uses.
# An agent is just code that builds these messages automatically and loops.

SYSTEM_PROMPT = """
You are a senior data architect assistant.
You give precise, technical answers without filler phrases.
Always cite concrete numbers when discussing performance or scale.
""".strip()

USER_MESSAGE = """
Explain the difference between a data lake, a data warehouse,
and a data lakehouse. Focus on when an architect would choose each.
""".strip()


# ── 3. Token estimation BEFORE the call ───────────────────────────────────────
# IMPORTANT: Mistral does NOT expose a token-counting endpoint in their SDK.
# The official approach is the `mistral-common` open-source tokenizer, but it
# requires downloading the tokenizer file from HuggingFace Hub at runtime.
#
# For pre-flight budget checks in production agents, practitioners use one of:
#   Option A: mistral-common + huggingface_hub (exact, requires internet + HF token)
#             from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
#             tok = MistralTokenizer.from_hf_hub('mistralai/Mistral-Large-Instruct-2411')
#
#   Option B: Word-count heuristic (shown here) — fast, no dependencies, ~10% error
#             Rule of thumb: 1 token ≈ 0.75 words (or ~4 characters) for English text
#
#   Option C: Call the API and read response.usage (the ground truth, shown in Step D)
#
# In agent loops, Option B gates rough budget decisions; Option C logs actuals.

def estimate_tokens_preflight(system: str, user: str) -> int:
    """
    Fast pre-flight token estimate using the 4-char-per-token rule of thumb.
    Accurate to within ~10–15% for English technical prose.
    Add ~3 tokens per message for Mistral's chat formatting overhead.
    """
    combined = f"{system}\n\n{user}"
    char_count = len(combined)
    estimated  = (char_count // 4) + 6   # +6 for two message format tokens
    return estimated


# ── 4. The actual API call ─────────────────────────────────────────────────────

def call_llm(client: Mistral, system: str, user: str):
    """
    One bare API call. No framework. No magic.
    This is what LangChain, LangGraph, and every agent framework does under the hood.

    Key parameters:
      temperature=0    → deterministic output, essential for structured data work
      max_tokens       → always set this in agents to cap runaway responses
    """
    response = client.chat.complete(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0,    # deterministic — critical for agent tool calls
        max_tokens=1024,  # always cap this in agents
    )
    return response


# ── 5. Usage report ────────────────────────────────────────────────────────────

def print_usage_report(preflight_tokens: int, response):
    """
    Everything an architect needs to know about one LLM call.
    In production agents, you'd log this per step, per task, per user session.

    Mistral SDK field names (different from Gemini!):
      response.usage.prompt_tokens       ← input token count
      response.usage.completion_tokens   ← output token count
      response.usage.total_tokens        ← sum of both
    """
    usage = response.usage

    input_tokens  = usage.prompt_tokens       # NOT prompt_token_count (that's Gemini)
    output_tokens = usage.completion_tokens   # NOT candidates_token_count (that's Gemini)
    total_tokens  = usage.total_tokens

    input_cost  = (input_tokens  / 1_000_000) * COST_PER_1M_INPUT
    output_cost = (output_tokens / 1_000_000) * COST_PER_1M_OUTPUT
    total_cost  = input_cost + output_cost

    print("\n" + "=" * 60)
    print("  TOKEN & COST REPORT")
    print("=" * 60)
    print(f"  Pre-flight estimate (heuristic) : {preflight_tokens:>6,} tokens")
    print(f"  Actual input tokens (API truth) : {input_tokens:>6,} tokens")
    print(f"  Estimation error                : {input_tokens - preflight_tokens:>+6,} tokens  "
          f"({abs(input_tokens - preflight_tokens) / input_tokens * 100:.1f}%)")
    print("-" * 60)
    print(f"  Output tokens                   : {output_tokens:>6,} tokens")
    print(f"  Total tokens this call          : {total_tokens:>6,} tokens")
    print("-" * 60)
    print(f"  Input cost                      :    ${input_cost:.6f}")
    print(f"  Output cost                     :    ${output_cost:.6f}")
    print(f"  Total cost this call            :    ${total_cost:.6f}")
    print("=" * 60)

    # Architect's perspective: what does this cost at scale?
    calls_per_day = 1_000
    daily_cost    = total_cost * calls_per_day
    monthly_cost  = daily_cost * 30
    print(f"\n  At {calls_per_day:,} calls/day:")
    print(f"    Daily cost   : ${daily_cost:.2f}")
    print(f"    Monthly cost : ${monthly_cost:.2f}")
    print("=" * 60)

    # Context window awareness — mistral-large-latest: 128K tokens
    context_window = 128_000
    pct_used = (total_tokens / context_window) * 100
    print(f"\n  Context window usage: {pct_used:.3f}% of {context_window:,} token budget")
    print(f"  Remaining budget   : {context_window - total_tokens:,} tokens")
    print("  (In an agent loop, this remaining budget shrinks with every step)")
    print("=" * 60)


# ── 6. Main ────────────────────────────────────────────────────────────────────

def main():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not set. Add it to your .env file.")

    client = Mistral(api_key=api_key)

    print(f"\nModel          : {MODEL}")
    print(f"System prompt  : {len(SYSTEM_PROMPT)} chars")
    print(f"User message   : {len(USER_MESSAGE)} chars")

    # Step A: estimate tokens BEFORE sending (the architect's pre-flight check)
    print("\nEstimating tokens (pre-flight heuristic)...")
    preflight_tokens = estimate_tokens_preflight(SYSTEM_PROMPT, USER_MESSAGE)
    print(f"Pre-flight estimate: ~{preflight_tokens:,} input tokens")

    # Step B: send the actual call
    print("\nSending request to Mistral...")
    response = call_llm(client, SYSTEM_PROMPT, USER_MESSAGE)

    # Step C: print the model's answer
    # Mistral: response.choices[0].message.content  (NOT response.text — that's Gemini)
    answer = response.choices[0].message.content
    print("\n" + "─" * 60)
    print("MODEL RESPONSE:")
    print("─" * 60)
    print(answer)

    # Step D: full usage report — response.usage is the ground truth token count
    print_usage_report(preflight_tokens, response)

    # ── EXPERIMENT PROMPTS ─────────────────────────────────────────────────────
    # After running once, try these to build intuition:
    #
    # 1. Make the system prompt much longer (add 500 words of instructions).
    #    Watch how input tokens jump. Output tokens barely change.
    #    Lesson: verbose system prompts are expensive at scale.
    #
    # 2. Ask for a very detailed response (add "Give a 2000 word answer").
    #    Watch output tokens jump. Cost multiplies.
    #    Lesson: max_tokens is a cost control lever.
    #
    # 3. Add a 5000-word document to the user message (paste any Wikipedia article).
    #    Watch input tokens explode.
    #    Lesson: RAG (retrieval) must be selective — don't dump whole documents in.
    #
    # 4. Run the same call 3 times. Input tokens should be identical each time.
    #    Output tokens will vary slightly even at temperature=0.
    #    Lesson: small non-determinism exists in output length regardless of temp.

if __name__ == "__main__":
    main()