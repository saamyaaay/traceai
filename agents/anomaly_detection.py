# aml_investigation_platform/agents/anomaly_detection.py

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from db.sqlite_db import AMLDatabase
from sklearn.preprocessing import LabelEncoder

class AnomalyDetectionAgent:
    def __init__(self):
        """Initialize the agent with database connection."""
        self.db = AMLDatabase()
        self.model = IsolationForest(contamination=0.01, random_state=42)  # 1% anomalies
        self.label_encoder = LabelEncoder()

    def prepare_features(self, df):
        """Prepare features for anomaly detection."""
        print("🔧 Preparing features...")
        features = df[['step', 'amount']].copy()
        features['type_encoded'] = self.label_encoder.fit_transform(df['type'])
        return features

    def detect_anomalies(self, df):
        """Detect anomalies using Isolation Forest."""
        print("🕵️‍♂️ Detecting anomalies...")
        features = self.prepare_features(df)
        self.model.fit(features)
        predictions = self.model.predict(features)  # -1 = anomaly
        df['anomaly_score'] = self.model.score_samples(features)
        df['is_anomaly'] = (predictions == -1).astype(int)
        return df

    def analyze(self, df):
        """Analyze transactions and flag anomalies."""
        print(f"📊 Analyzing {len(df)} transactions for anomalies...")
        df = self.detect_anomalies(df)

        # Flag only top anomalies into the DB
        anomalies = df[df['is_anomaly'] == 1]
        for _, row in anomalies.iterrows():
            self.db.flag_case(
                transaction_id=int(row['id']),
                agent_type="AnomalyDetection",
                flag_reason=f"Anomaly detected (score: {row['anomaly_score']:.2f})"
            )

        print(f"✅ Flagged {len(anomalies)} anomalies.")
        return df

# Run standalone
if __name__ == "__main__":
    from utils.data_loader import load_paysim_data

    print("\n📥 Loading transaction data...")
    df = load_paysim_data()

    # Sample for testing
    df = df.sample(10000, random_state=42).reset_index(drop=True)
    df = df.reset_index().rename(columns={"index": "id"})  # Ensure 'id' field for DB mapping

    # Insert into DB
    db = AMLDatabase()
    db.insert_transactions(df)

    # Run anomaly detection
    agent = AnomalyDetectionAgent()
    df_with_anomalies = agent.analyze(df)

    # Display results
    flagged_df = db.get_flagged_cases()
    print("\n📋 Flagged Cases:")
    print(flagged_df.head())
