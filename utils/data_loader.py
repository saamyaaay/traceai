import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Set dataset and output paths
DATA_PATH = "data/paysim.csv"
PLOT_DIR = "data"

def load_paysim_data(data_path=DATA_PATH):
    """Load and clean the PaySim dataset."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"❌ Dataset not found at {data_path}. Please place it in the 'data/' folder.")

    print("📥 Loading dataset...")
    df = pd.read_csv(data_path)

    # Check for missing values
    print("\n🔍 Missing values in each column:")
    print(df.isnull().sum())

    # Ensure correct data types
    df['amount'] = df['amount'].astype(float)
    df['isFraud'] = df['isFraud'].astype(int)
    df['isFlaggedFraud'] = df['isFlaggedFraud'].astype(int)

    # Remove duplicates
    df = df.drop_duplicates()

    # Dataset summary
    print("\n📊 Dataset Info:")
    print(df.info())

    print("\n📌 Transaction Type Counts:")
    print(df['type'].value_counts())

    print("\n⚠️ Fraud vs Non-Fraud Counts:")
    print(df['isFraud'].value_counts())

    return df

def generate_plots(df, plot_dir=PLOT_DIR):
    """Generate and save EDA plots."""
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    # Plot 1: Transaction Types by Fraud Status
    plt.figure(figsize=(10, 6))
    sns.countplot(x='type', hue='isFraud', data=df, palette='Set2')
    plt.title("Transaction Types by Fraud Status")
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, "transaction_types.png"))
    plt.close()

    # Plot 2: Amount Distribution below 95th percentile
    plt.figure(figsize=(10, 6))
    sns.histplot(df[df['amount'] < df['amount'].quantile(0.95)]['amount'],
                 bins=50, kde=True, color='skyblue')
    plt.title("Transaction Amount Distribution (Below 95th Percentile)")
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, "amount_distribution.png"))
    plt.close()

    print("✅ Plots saved in 'data/' folder.")

if __name__ == "__main__":
    df = load_paysim_data()
    print("\n🖼️ Generating plots...")
    generate_plots(df)
    print("\n✅ First 5 rows of cleaned dataset:")
    print(df.head())
