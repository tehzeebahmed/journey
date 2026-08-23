import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel, Field
CURR_PATH = Path(__file__).parent

# -------------------------------------------------------------------
# Pydantic Schemas for Structured Data Validation
# -------------------------------------------------------------------
class DailyCallLog(BaseModel):
    date: str = Field(description="Date of the calls logged (YYYY-MM-DD)")
    calls_attempted: int = Field(description="Total calls dialed out")
    calls_connected: int = Field(description="Calls answered by customers (Attended)")
    right_party_contacts: int = Field(description="Calls where actual debtor was reached")
    promises_to_pay: int = Field(description="Commitments secured from debtor to pay")


class AgentMonthlyMetrics(BaseModel):
    agent_id: str = Field(description="Unique identifier for the agent")
    agent_name: str = Field(description="Full name of the collection agent")
    reporting_month: str = Field(description="Target reporting month (YYYY-MM)")
    portfolio_bucket: str = Field(description="Delinquency bucket (e.g., 30 DPD, 60 DPD)")
    
    # Aggregated Monthly Totals
    total_calls_attended: int = Field(description="Total answered calls handled this month")
    total_amount_collected: float = Field(description="Total cash volume recovered in the month")
    target_recovery_amount: float = Field(description="Assigned monthly collection target")
    incentive_earned: float = Field(description="Bonus payouts achieved based on metrics")
    
    # Granular Breakdown
    daily_logs: list[DailyCallLog] = Field(description="Day-by-day agent operational breakdown")


# -------------------------------------------------------------------
# Core Data Generation Logic
# -------------------------------------------------------------------
def generate_single_month(agent_id: str, name: str, bucket: str, year: int, month: int) -> AgentMonthlyMetrics:
    """Generates operational metrics for one agent for one specific month."""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

    daily_logs = []
    running_attended_total = 0
    running_ptp_total = 0

    current_day = start_date
    while current_day <= end_date:
        # Skip Sundays (standard rest day in BFSI collections operations)
        if current_day.weekday() == 6:
            current_day += timedelta(days=1)
            continue

        # Build dynamic performance variation based on randomized day conditions
        attempted = random.randint(110, 190)
        connected = random.randint(int(attempted * 0.40), int(attempted * 0.65))
        rpc = random.randint(int(connected * 0.35), int(connected * 0.55))
        ptp = random.randint(int(rpc * 0.20), int(rpc * 0.45))

        running_attended_total += connected
        running_ptp_total += ptp

        daily_logs.append(
            DailyCallLog(
                date=current_day.strftime("%Y-%m-%d"),
                calls_attempted=attempted,
                calls_connected=connected,
                right_party_contacts=rpc,
                promises_to_pay=ptp
            )
        )
        current_day += timedelta(days=1)

    # Asset recovery configuration
    target = float(random.choice([400000, 500000, 600000]))  # Static bracket assignments
    average_ticket_size = random.randint(2800, 4200)
    actual_collected = round((running_ptp_total * random.uniform(0.55, 0.68)) * average_ticket_size, 2)

    achievement_ratio = actual_collected / target
    incentive = round(actual_collected * 0.025, 2) if achievement_ratio >= 1.0 else 0.0

    return AgentMonthlyMetrics(
        agent_id=agent_id,
        agent_name=name,
        reporting_month=start_date.strftime("%Y-%m"),
        portfolio_bucket=bucket,
        total_calls_attended=running_attended_total,
        total_amount_collected=actual_collected,
        target_recovery_amount=target,
        incentive_earned=incentive,
        daily_logs=daily_logs
    )


def generate_bulk_collection_data() -> list[dict]:
    """Loops over a matrix of 20 agents across June, July, and August 2026."""
    # 20 Mock Indian BFSI Agents
    agent_roster = [
        {"id": f"AGT-2026-{1000 + i}", "name": name, "bucket": bucket}
        for i, (name, bucket) in enumerate([
            ("Rahul Sharma", "Early Stage (1-30 DPD)"), ("Priya Patel", "Early Stage (1-30 DPD)"),
            ("Amit Singh", "Early Stage (1-30 DPD)"), ("Sneha Reddy", "Early Stage (1-30 DPD)"),
            ("Vikram Malhotra", "Early Stage (1-30 DPD)"), ("Ananya Iyer", "Early Stage (1-30 DPD)"),
            ("Rohan Das", "Mid Stage (31-60 DPD)"), ("Kriti Verma", "Mid Stage (31-60 DPD)"),
            ("Deepak Joshi", "Mid Stage (31-60 DPD)"), ("Meera Nair", "Mid Stage (31-60 DPD)"),
            ("Sanjay Gupta", "Mid Stage (31-60 DPD)"), ("Pooja Rao", "Mid Stage (31-60 DPD)"),
            ("Arjun Mehta", "Late Stage (61-90 DPD)"), ("Divya Choudhary", "Late Stage (61-90 DPD)"),
            ("Karan Johar", "Late Stage (61-90 DPD)"), ("Nisha Gill", "Late Stage (61-90 DPD)"),
            ("Abhishek Mishra", "Write-Off Pool (>90 DPD)"), ("Shweta Tiwari", "Write-Off Pool (>90 DPD)"),
            ("Rajesh Kumar", "Write-Off Pool (>90 DPD)"), ("Aarti Saxena", "Write-Off Pool (>90 DPD)")
        ])
    ]

    target_periods = [(2026, 6), (2026, 7), (2026, 8)] # June, July, August
    master_records = []

    for agent in agent_roster:
        for year, month in target_periods:
            monthly_metric_profile = generate_single_month(
                agent_id=agent["id"],
                name=agent["name"],
                bucket=agent["bucket"],
                year=year,
                month=month
            )
            # Add to list output as a plain, serializable layout
            master_records.append(monthly_metric_profile.model_dump())

    return master_records


# -------------------------------------------------------------------
# Execution Block
# -------------------------------------------------------------------
if __name__ == "__main__":
    OUTPUT_FILE_PATH = CURR_PATH.joinpath("v3_agent_performance_report.json")
    
    # Run loop logic
    all_agent_data = generate_bulk_collection_data()
    
    try:
        with open(OUTPUT_FILE_PATH, "w") as file_out:
            json.dump(all_agent_data, file_out, indent=4)
            
        print("✅ Bulk Generation Complete!")
        print(f"📁 Output File Created: {OUTPUT_FILE_PATH}")
        print(f"📊 Total Monthly Records Generated: {len(all_agent_data)} (20 Agents × 3 Months)")
        
    except Exception as error_msg:
        print(f"❌ Processing aborted: {error_msg}")
        raise
