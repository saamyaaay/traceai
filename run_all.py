
# aml_investigation_platform/run_all.py
import pandas as pd
from db.sqlite_db import AMLDatabase
from agents.transaction_analysis import TransactionAnalysisAgent
from agents.anomaly_detection import AnomalyDetectionAgent
from agents.investigation import InvestigationAgent
from utils.data_loader import load_paysim_data
from agents.regulatory_reporting import RegulatoryReportingAgent

def run_aml_platform():
    print("📈 Starting AML Investigation Platform...")
    db = AMLDatabase()

    # Load and prepare data
    print("📥 Loading and preparing transaction data...")
    df = load_paysim_data()
    df = df.sample(10000, random_state=42).reset_index(drop=True)
    df = df.reset_index().rename(columns={"index": "id"})
    db.insert_transactions(df)

    # Run agents
    print("🧠 Running Transaction Analysis Agent...")
    transaction_agent = TransactionAnalysisAgent()
    transaction_agent.analyze(df)

    print("🧠 Running Anomaly Detection Agent...")
    anomaly_agent = AnomalyDetectionAgent()
    anomaly_agent.analyze(df)

    print("🕵️ Running Investigation Agent...")
    investigation_agent = InvestigationAgent()
    investigation_reports = investigation_agent.investigate()

    print("📤 Running Regulatory Reporting Agent...")
    reporting_agent = RegulatoryReportingAgent()
    reporting_agent.generate_reports()

    print("✅ AML Platform workflow completed!")
    return investigation_reports

if __name__ == "__main__":
    reports = run_aml_platform()
    for tid, report in reports.items():
        print(f"\n📄 SAR Report for Transaction ID {tid}:\n{report}")
