import os
import pandas as pd
import datetime
import random
from db.sqlite_db import AMLDatabase

# Read USE_LLM flag from environment—default to False for now
USE_LLM = os.getenv("USE_LLM", "False").lower() in ("true", "1", "yes")

# Try importing GPT4All only if USE_LLM is True
if USE_LLM:
    try:
        from langchain_community.llms import GPT4All
        from langchain.prompts import PromptTemplate
        from langchain_core.runnables import RunnableSequence
        LLM_AVAILABLE = True
    except ImportError:
        LLM_AVAILABLE = False
else:
    LLM_AVAILABLE = False


class InvestigationAgent:
    def __init__(self):
        """Initialize database and optional LLM pipeline."""
        self.db = AMLDatabase()
        self.use_llm = LLM_AVAILABLE

        if self.use_llm:
            model_path = os.path.join("models", "mistral-7b.Q4_0.gguf")
            self.llm = GPT4All(model=model_path, backend="llama")
            self.prompt_template = PromptTemplate(
                input_variables=["transaction_id", "agent_type", "flag_reason", "mock_evidence", "date"],
                template=(
                    "Generate a Suspicious Activity Report (SAR) for transaction ID {transaction_id}, "
                    "flagged by {agent_type} due to: {flag_reason}. "
                    "Include the following evidence: {mock_evidence}. "
                    "Report generated on {date}."
                )
            )
            # New chaining syntax
            self.chain = self.prompt_template | self.llm

    def generate_mock_evidence(self, transaction):
        """Generate simple mock evidence for a transaction."""
        mock_ips = [f"192.168.{random.randint(0,255)}.{random.randint(0,255)}" for _ in range(3)]
        count = random.randint(5,15)
        return f"IP Logs: {', '.join(mock_ips)}. Previous {count} similar transfers."

    def generate_report(self, transaction_id, agent_type, flag_reason, transaction_data):
        """Return either an LLM-generated or fallback SAR."""
        mock_evidence = self.generate_mock_evidence(transaction_data)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.use_llm:
            return self.chain.invoke({
                "transaction_id": transaction_id,
                "agent_type": agent_type,
                "flag_reason": flag_reason,
                "mock_evidence": mock_evidence,
                "date": timestamp
            })
        # Fallback template
        return (
            f"🔎 Suspicious Activity Report (SAR)\n"
            f"Transaction ID: {transaction_id}\n"
            f"Flagged By: {agent_type}\n"
            f"Reason: {flag_reason}\n"
            f"Evidence: {mock_evidence}\n"
            f"Generated On: {timestamp}\n"
        )

    def investigate(self, max_cases=3):
        """Generate SARs for up to `max_cases` flagged transactions."""
        print("🕵️‍ Investigating flagged cases…")
        flagged_df = self.db.get_flagged_cases()
        if flagged_df.empty:
            print("⚠️ No flagged cases.")
            return {}

        # Use iloc for positional slicing to avoid indexing issues
        flagged_df = flagged_df.reset_index(drop=True)  # Ensure clean index
        flagged_df = flagged_df.iloc[:min(max_cases, len(flagged_df))]  # Limit to max_cases

        reports = {}
        for _, row in flagged_df.iterrows():
            tid = row["transaction_id"]
            report = self.generate_report(
                transaction_id=tid,
                agent_type=row["agent_type"],
                flag_reason=row["flag_reason"],
                transaction_data=row
            )
            reports[tid] = report
            print(f"✅ Generated SAR for Transaction ID {tid}")

        return reports

if __name__ == "__main__":
    # Quick local test
    from utils.data_loader import load_paysim_data
    from agents.transaction_analysis import TransactionAnalysisAgent
    from agents.anomaly_detection import AnomalyDetectionAgent

    # Load & prep
    df = load_paysim_data().sample(10000, random_state=42).reset_index(drop=True)
    df = df.reset_index().rename(columns={"index": "id"})
    AMLDatabase().insert_transactions(df)

    # Run upstream agents
    TransactionAnalysisAgent().analyze(df)
    AnomalyDetectionAgent().analyze(df)

    # Investigate only first 3
    agent = InvestigationAgent()
    sar_reports = agent.investigate(max_cases=3)
    for tid, text in sar_reports.items():
        print(f"\n--- SAR {tid} ---\n{text}")