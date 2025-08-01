import sqlite3
import pandas as pd
import os

class AMLDatabase:
    def __init__(self, db_path="db/aml_database.db"):
        """Initialize the SQLite database connection and create tables."""
        self.db_path = db_path
        self.conn = None
        self._ensure_directory()
        self.create_tables()

    def _ensure_directory(self):
        """Ensure the database folder exists."""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def connect(self):
        """Open database connection."""
        self.conn = sqlite3.connect(self.db_path)

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_tables(self):
        """Create necessary tables."""
        self.connect()
        cursor = self.conn.cursor()

        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                step INTEGER,
                type TEXT,
                amount REAL,
                nameOrig TEXT,
                nameDest TEXT,
                isFraud INTEGER,
                isFlaggedFraud INTEGER
            )
        ''')

        # Flagged cases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flagged_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                agent_type TEXT,
                flag_reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id)
            )
        ''')

        self.conn.commit()
        self.close()

    def insert_transactions(self, df: pd.DataFrame):
        """Insert a DataFrame of transactions into the database."""
        if df.empty:
            print("⚠️ DataFrame is empty. No transactions inserted.")
            return
        self.connect()
        df.to_sql('transactions', self.conn, if_exists='replace', index=False)
        self.conn.commit()
        self.close()
        print(f"✅ Inserted {len(df)} transactions into the database.")

    def flag_case(self, transaction_id: int, agent_type: str, flag_reason: str):
        """Flag a specific transaction."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO flagged_cases (transaction_id, agent_type, flag_reason)
            VALUES (?, ?, ?)
        ''', (transaction_id, agent_type, flag_reason))
        self.conn.commit()
        self.close()
        print(f"🚩 Flagged transaction ID {transaction_id} - Reason: {flag_reason}")

    def get_flagged_cases(self) -> pd.DataFrame:
        """Retrieve all flagged cases as a DataFrame."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT fc.id AS flag_id, fc.transaction_id, fc.agent_type, fc.flag_reason, fc.timestamp,
                   t.step, t.type, t.amount, t.nameOrig, t.nameDest, t.isFraud, t.isFlaggedFraud
            FROM flagged_cases fc
            JOIN transactions t ON fc.transaction_id = t.id
        ''')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        df = df.reset_index(drop=True)  # Ensure a clean RangeIndex
        self.close()
        return df

# Example usage
if __name__ == "__main__":
    from utils.data_loader import load_paysim_data

    print("\n📥 Loading and inserting transactions...")
    db = AMLDatabase()
    df = load_paysim_data()
    db.insert_transactions(df)

    print("\n🚩 Flagging example case...")
    db.flag_case(transaction_id=1, agent_type="AnomalyDetection", flag_reason="Unusual amount")

    print("\n📋 Flagged Cases:")
    flagged_df = db.get_flagged_cases()
    print(flagged_df.head())