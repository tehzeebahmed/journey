Agent logs in → sees their account queue
     ↓
Picks account → asks copilot "Brief me on ACC-0892"
     ↓
Copilot responds with:
  - Days overdue, amount, last payment date
  - Previous call history and promises made
  - Best contact time based on past responses
  - Suggested script for this customer profile
     ↓
Agent makes call → logs outcome via natural language
"Customer agreed to pay INR 20,000 by August 25"
     ↓
Copilot automatically:
  - Logs the interaction
  - Creates a promise-to-pay record
  - Notifies RM via summary
  - Sets a follow-up flag for August 26

  System Architecture:
  User (call centre agent)
        ↓
Conversational Loop (multi-turn chat)
        ↓
Intent Router — what is the agent asking?
  ├── "brief me on account"    → Account Summary Agent
  ├── "payment history"        → Payment History Agent
  ├── "log outcome"            → Journal Agent (writes to log)
  ├── "flag for legal"         → Escalation Agent
  └── "show my queue"          → Queue Agent
        ↓
RAG — collections policy documents
(what script to use, what settlement % is allowed, escalation rules)
        ↓
Response generated → shown to agent
        ↓
Episodic memory — remembers this conversation
so RM gets full context when they review


Agents:
account_brief    → AccountBriefAgent
                   reads accounts.json + call_log.json
                   returns: customer summary + risk level + 
                            previous promises + suggested script

payment_history  → PaymentHistoryAgent  
                   reads accounts.json + call_log.json
                   returns: full payment timeline

log_promise      → JournalAgent
                   writes to call_log.json
                   sets promise_amount, promise_date in state
                   triggers RM summary if home loan

escalate         → EscalationAgent
                   checks policy via RAG
                   writes escalation record
                   sets escalate_to_legal = True in state

show_queue       → QueueAgent
                   reads accounts.json
                   returns: all accounts assigned to this agent
                            sorted by overdue_days descending
                            