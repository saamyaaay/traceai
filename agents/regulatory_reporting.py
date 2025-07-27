import os
import subprocess
from dotenv import load_dotenv
from db.sqlite_db import AMLDatabase
from agents.investigation import InvestigationAgent

class RegulatoryReportingAgent:
    def __init__(self):
        """Initialize the agent with DB."""
        load_dotenv()
        self.db = AMLDatabase()
        self.investigation_agent = InvestigationAgent()

    def save_to_file(self, report, transaction_id):
        """Save SAR to a text file."""
        output_dir = "reports"
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"sar_{transaction_id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"📥 Saved SAR for Transaction ID {transaction_id} to {file_path}")
        return file_path

    def send_email_with_node(self, transaction_id):
        """Call Node.js script to send email."""
        try:
            print(f"📧 Sending email for Transaction ID {transaction_id}...")
            subprocess.run(["node", "sendMail.js", str(transaction_id)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to send email for Transaction ID {transaction_id}: {e}")

    def generate_reports(self, recipient_email="saamyasingla24@gmail.com", max_emails=10):
        """Generate and deliver SARs for flagged transactions with a limit."""
        print("📤 Starting regulatory report generation...")
        try:
            reports = self.investigation_agent.investigate()
        except Exception as e:
            print(f"❌ Investigation failed: {e}")
            return {}

        email_count = 0
        for transaction_id, report in reports.items():
            if email_count < max_emails:  # Simple limit without database check
                self.save_to_file(report, transaction_id)
                self.send_email_with_node(transaction_id)
                email_count += 1

        print(f"✅ Generated {email_count} SAR emails (limited to {max_emails}).")
        return reports

if __name__ == "__main__":
    from utils.data_loader import load_paysim_data
    from agents.transaction_analysis import TransactionAnalysisAgent
    from agents.anomaly_detection import AnomalyDetectionAgent

    load_dotenv()

    print("\n📥 Loading data...")
    df = load_paysim_data()
    df = df.sample(10000, random_state=42).reset_index(drop=True)  # Fixed to 10,000 rows
    df = df.reset_index().rename(columns={"index": "id"})

    db = AMLDatabase()
    db.insert_transactions(df)

    print("\n🔍 Running Transaction Analysis...")
    TransactionAnalysisAgent().analyze(df)

    print("\n🔍 Running Anomaly Detection...")
    AnomalyDetectionAgent().analyze(df)

    print("\n📋 Running Investigation Agent...")
    InvestigationAgent().investigate()

    print("\n📨 Running Regulatory Reporting Agent...")
    reporter = RegulatoryReportingAgent()
    reports = reporter.generate_reports(recipient_email="saamyasingla24@gmail.com")