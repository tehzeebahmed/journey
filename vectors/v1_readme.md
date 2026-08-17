The Archetechture is :


                    ┌─────────────────────┐
                    │ Transactions JSON   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Data File Validation│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Chunk Generator     │
                    │ CHUNK_SIZE = 100    │
                    └──────────┬──────────┘
                               │
                ┌──────────────▼──────────────┐
                │                             │
                ▼                             ▼
       Episodic Memory Check          Position/Limit Lookup
                │                             │
                └──────────────┬──────────────┘
                               ▼
                     ComplianceState
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        Data Quality      Reconciliation    Regulatory
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                     Final ComplianceState
                               │
                               ▼
                     Aggregate Results
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        Results / Checkpoint            Episodic Memory
                │
                ▼
             LLM Report
