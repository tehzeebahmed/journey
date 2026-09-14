"""
audit logger
This will be used for logging all events happening in the flow of original script(neo4j_clcal_regl_aff_large.py)

"""

import json
import uuid
import hashlib
import threading
from pathlib import Path
from datetime import datetime, timezone

def summarize_results(records):
    """build a summary of results for Regulatory affiars filing on clinical studies"""
    canonical = json.dumps(records, sort_keys=True, default=str)
    result_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest() 
    summary = {"row_count": len(records), "result_hash": result_hash}
    numeric_fields =   {}
    for row in records:
        if not isinstance(row, dict):
            continue
        for key, value in row.items():
            if isinstance(value, bool):
                continue
            if isinstance (value, (int, float)):
                numeric_fields.setdefault(key, []).append(value)
        for key, values in numeric_fields.items():
            summary[f"{key}_min"] = min(values)
            summary[f"{key}_max"] = max(values)
            summary[f"{key}_mean"] = round(sum(values)/ len(values), 3)

        return summary

class AuditLogger():
    """JSONL audit logger"""
    def __init__(self, path = "clinical_copilot_audit.jsonl"):
        self.path = Path(path)
        self._lock = threading.Lock()
    def log(
            self, 
            question, 
            classified_intent, 
            cypher = None, 
            parameters = None,
            result_summary = None,
            narrative = None,
            query_key = None,
            model = None, 
            latency_ms = None
    ):
        """Write one audit record each time. If more params are required can be added later after latency"""
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "classified_intent": classified_intent,
            "cypher": cypher,
            "parameters": parameters,
            "result_summary": result_summary,
            "narrative": narrative,
            "query_key": query_key,
            "model": model,
            "latency_ms": latency_ms
        }
        line = json.dumps(event, default=str)
        with self._lock:
            with open(self.path, "a") as append_file:
                append_file.write(line + "\n")
        return event["event_id"]
def verify_hash(records, expected_hash):
    """rechecks the hash value if we can track back (lineage) of the data and the regulatory report"""
    canonical = json.dumps(records, sort_keys = True, default = str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest() == expected_hash