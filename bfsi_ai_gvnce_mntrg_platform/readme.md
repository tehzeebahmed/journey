Bult Order:
Week 1 — Module A: Data Contract Monitor
  Day 1-2: Define contract schema (Pydantic)
  Day 3-4: Contract validator agent
  Day 5:   Violation reporter + alert system

Week 2 — Module B: LLM Eval Pipeline
  Day 1-2: Golden dataset builder
  Day 3-4: Nightly eval runner
  Day 5:   Drift detector + auto-correction logic

Week 3 — Module C: AML Pattern Detector
  Day 1-2: Transaction graph builder
  Day 3-4: Pattern detection (circular, fan-out, velocity)
  Day 5:   Risk scorer + alert generator

Week 4 — Integration
  Day 1-2: Unified governance report generator (LLM)
  Day 3-4: Scheduler (runs automatically every 24 hours)
  Day 5:   End-to-end test + portfolio documentation


Layer 1 — Data Contract Monitor
  Watches incoming data for schema drift, quality violations
  "The transaction schema changed — 3 downstream AI agents will break"

Layer 2 — LLM Response Validator  
  Tests AI agent responses against a golden eval set weekly
  "Agent accuracy dropped from 94% to 71% — model drift detected"

Layer 3 — AML Pattern Detector
  Graph-based transaction analysis
  "New circular money flow pattern detected — not in training data"

Layer 4 — Governance Dashboard
  Unified view for Head of AI / CRO
  Red/amber/green status per layer
  Auto-generated incident report when drift detected

  The core idea — a continuous testing loop
  Every 24 hours at midnight:
  Run 50 test transactions through your AI agents
  Compare outputs against known correct answers
  Calculate accuracy score
  If score drops below threshold → raise alert → auto-correct
  Generate governance report for CRO

Three Modules together:
Module A — Data Contract Monitor    (Option C)
Module B — LLM Eval Pipeline       (Module 9 MLOps)  
Module C — AML Pattern Detector    (your idea — pure Python, no Neo4j yet)

What it does:
Producer: payments team pushes daily transaction file
Contract: {
  "transaction_id": "string, required",
  "amount":         "float, required, > 0",
  "currency":       "string, required, enum: [INR, USD, GBP]",
  "timestamp":      "ISO8601, required",
  "account_id":     "string, required, format: ACC[0-9]{3}"
}

Violation detected:
  - amount: null (5 records)
  - currency: "EURO" instead of "EUR" (12 records)
  - new field "branch_code" not in contract (all records)

Alert: "3 contract violations — 17 records affected
        Downstream agents: AML detector, credit scorer
        Impact: potential false negatives on fraud detection"

Module B — LLM Eval Pipeline
The golden dataset concept

At deployment, you create a golden dataset — 50 representative test cases with known correct answers. Every night, you run all 50 through your AI agent and score the results.
Golden dataset example (collections agent):
  Input:  "ACC002 — Priya Sharma — 92 days — INR 128,000"
  Expected output: decision = "escalate"
  Expected reason: mentions "90 days" AND "INR 50,000 threshold"

Nightly eval run:
  Day 1:   48/50 correct = 96% ✓
  Day 30:  47/50 correct = 94% ✓
  Day 90:  41/50 correct = 82% ⚠️ WARN
  Day 180: 35/50 correct = 70% 🔴 ALERT — drift detected

Module C — AML Pattern Detector:
Graph relationships in pure Python

No Neo4j for now — we simulate graph relationships with dicts. The concept is identical, the implementation is simpler.

# Transaction graph — who sent money to whom
GRAPH = {
    "ACC001": ["ACC005", "ACC009"],          # ACC001 sent to these
    "ACC005": ["ACC009", "ACC012"],
    "ACC009": ["ACC001"],                    # circular — ACC001 → ACC005 → ACC009 → ACC001
    "ACC012": ["ACC015", "ACC020", "ACC003"] # fan-out — one account to many
}

# AML patterns to detect:
# 1. Circular flow     — money goes in a circle (layering)
# 2. Fan-out          — one account sends to many (structuring)
# 3. Rapid movement   — money moves through 3+ accounts in 24 hours (velocity)
# 4. Round amounts    — suspiciously round numbers (INR 100,000 exactly)
# 5. New account spike — dormant account suddenly active

The unified governance dashboard output
AI GOVERNANCE REPORT — 23 August 2026
Generated: 06:00:00
════════════════════════════════════════

SYSTEM HEALTH OVERVIEW
  Data Contracts   : 🔴 2 violations detected
  LLM Performance  : ⚠️  82% accuracy (threshold: 85%)
  AML Detection    : ✅  No new patterns
  Overall Status   : AMBER — action required

DATA CONTRACT VIOLATIONS
  payments_daily.json — 3 violations:
  • amount: null in 5 records (agents skipping these)
  • currency: "EURO" found (12 records — wrong format)
  • new field branch_code not in contract
  Action: payments team notified automatically

LLM PERFORMANCE DEGRADATION
  Collections agent accuracy: 82% (was 96% at deployment)
  Failing test cases: escalation decisions (8/15 wrong)
  Root cause: LLM provider updated model on Aug 15
  Auto-correction: system prompt updated — re-eval pending

AML PATTERNS
  1,000 transactions scanned
  Circular flow detected: ACC001 → ACC005 → ACC009 → ACC001
  Total: INR 4,50,000 cycled in 48 hours
  Status: Flagged for compliance team review
════════════════════════════════════════

Data Contract
     │
     ├── Schema validation
     │      ├── New column
     │      ├── Missing column
     │      └── Duplicate record
     │
     ├── Data type validation
     │      ├── amount → float
     │      └── transaction_id → string
     │
     ├── Required field validation
     │      └── amount cannot be NULL
     │
     ├── Range validation
     │      └── amount >= 0
     │
     ├── Allowed value validation
     │      └── currency ∈ {INR, USD, EUR}
     │
     └── Pattern validation
            └── transaction_id matches regex