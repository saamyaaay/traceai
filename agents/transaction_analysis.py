# aml_investigation_platform/agents/transaction_analysis.py

import pandas as pd
import networkx as nx
from db.sqlite_db import AMLDatabase
from collections import defaultdict

class TransactionAnalysisAgent:
    def __init__(self):
        """Initialize the agent with database connection."""
        self.db = AMLDatabase()
        self.graph = nx.DiGraph()

    def build_transaction_network(self, df):
        """Build a directed graph from transaction data."""
        print("🔗 Building transaction graph...")
        for _, row in df.iterrows():
            source = row['nameOrig']
            target = row['nameDest']
            amount = row['amount']
            trans_type = row['type']
            self.graph.add_edge(source, target, amount=amount, type=trans_type)

    def detect_smurfing(self, min_transactions=5, max_amount=5000):
        """Detect smurfing: multiple small transactions from one source."""
        print("🧪 Detecting smurfing...")
        smurfing_flags = []
        for node in self.graph.nodes():
            outgoing = [(u, v, d) for u, v, d in self.graph.out_edges(node, data=True)]
            small_txns = [e for e in outgoing if e[2]['amount'] < max_amount]
            if len(small_txns) >= min_transactions:
                smurfing_flags.append((node, len(small_txns)))
        return smurfing_flags

    def detect_round_tripping(self, max_cycle_length=3):
        """Detect round-tripping: cycles in transaction flow."""
        print("🌀 Detecting round-tripping...")
        cycles = list(nx.simple_cycles(self.graph))
        round_tripping_flags = [cycle for cycle in cycles if len(cycle) <= max_cycle_length]
        return round_tripping_flags

    def analyze(self, df):
        """Analyze transactions and flag suspicious cases."""
        print(f"📊 Analyzing {len(df)} transactions...")
        self.build_transaction_network(df)

        # Detect smurfing
        smurfing_flags = self.detect_smurfing()
        for source, count in smurfing_flags:
            txn = df[df['nameOrig'] == source].head(1)
            if not txn.empty:
                transaction_id = int(txn['id'].values[0])
                self.db.flag_case(transaction_id, "TransactionAnalysis", f"Smurfing detected ({count} small txns)")

        # Detect round-tripping
        round_tripping_flags = self.detect_round_tripping()
        for cycle in round_tripping_flags:
            for account in cycle:
                txn = df[df['nameOrig'] == account].head(1)
                if not txn.empty:
                    transaction_id = int(txn['id'].values[0])
                    self.db.flag_case(transaction_id, "TransactionAnalysis", f"Round-tripping in cycle {cycle}")
                    break  # Only flag 1 transaction per cycle

        print(f"✅ Flagged {len(smurfing_flags) + len(round_tripping_flags)} cases.")

if __name__ == "__main__":
    from utils.data_loader import load_paysim_data

    print("\n📥 Loading transaction data...")
    df = load_paysim_data()

    # ✅ SAMPLE: Reduce dataset to 10,000 rows for testing
    df = df.sample(10000, random_state=42).reset_index(drop=True)
    df = df.reset_index().rename(columns={"index": "id"})  # Add unique 'id' field

    # Store to DB
    db = AMLDatabase()
    db.insert_transactions(df)

    # Analyze
    agent = TransactionAnalysisAgent()
    agent.analyze(df)

    # Display flagged results
    flagged_df = db.get_flagged_cases()
    print("\n📋 Flagged Cases:")
    print(flagged_df.head())
