import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import networkx as nx
from agents.transaction_analysis import TransactionAnalysisAgent
from agents.anomaly_detection import AnomalyDetectionAgent
from agents.investigation import InvestigationAgent
from agents.regulatory_reporting import RegulatoryReportingAgent
from db.sqlite_db import AMLDatabase
from utils.data_loader import load_paysim_data

# Set page configuration as the first Streamlit command
st.set_page_config(page_title="AML Investigation Dashboard", layout="wide")

# Initialize database outside cache
db = AMLDatabase()

# Load and prepare data
@st.cache_data
def load_data(_db):
    df = load_paysim_data()
    print(f"Loaded DataFrame shape: {df.shape}")  # Debug
    if len(df) < 10000:
        st.warning(f"Dataset has only {len(df)} rows, which is less than 10,000. Using all available data.")
        sampled_df = df
    else:
        sampled_df = df.sample(10000, random_state=42)  # Fixed to 10,000 rows
    print(f"Sampled DataFrame shape: {sampled_df.shape}")  # Debug
    sampled_df = sampled_df.reset_index(drop=True)
    sampled_df = sampled_df.reset_index().rename(columns={"index": "id"})
    print(f"Inserted {len(sampled_df)} transactions into DB")  # Debug
    _db.insert_transactions(sampled_df)
    return sampled_df

df = load_data(db)
print(f"df columns: {df.columns.tolist()}")  # Debug
print(f"df shape after load: {df.shape}")  # Debug
if df.empty:
    st.error("DataFrame is empty. No visualizations can be generated.")
elif not all(col in df.columns for col in ['step', 'amount', 'nameOrig', 'nameDest', 'type']):
    st.error("Missing required columns in DataFrame. Expected: step, amount, nameOrig, nameDest, type.")

st.title("AML Investigation Platform Dashboard")

# Sidebar for navigation and filters
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Transaction Network", "Anomaly Detection", "Investigation Summary", "Regulatory Reporting"])

# Add filters using the loaded df
st.sidebar.header("Filters")
min_step, max_step = st.sidebar.slider("Select Time Step Range", int(df['step'].min()), int(df['step'].max()), (int(df['step'].min()), int(df['step'].max())))
print(f"Slider range: min_step={min_step}, max_step={max_step}")  # Debug
transaction_types = ['All'] + list(df['type'].unique())
selected_type = st.sidebar.selectbox("Select Transaction Type", transaction_types)
print(f"Selected transaction type: {selected_type}")  # Debug

# Apply filters
filtered_df = df[(df['step'] >= min_step) & (df['step'] <= max_step)]
if selected_type != 'All':
    filtered_df = filtered_df[filtered_df['type'] == selected_type]
print(f"Filtered_df shape: {filtered_df.shape}")  # Debug
print(f"Filtered_df columns: {filtered_df.columns.tolist()}")  # Debug

# Initialize df_with_anomalies as empty DataFrame
df_with_anomalies = pd.DataFrame()

# Run agents in a separate function with fallback
def run_agents(_db, _filtered_df):
    ta_agent = TransactionAnalysisAgent()
    ad_agent = AnomalyDetectionAgent()
    inv_agent = InvestigationAgent()
    rr_agent = RegulatoryReportingAgent()
    try:
        ta_agent.analyze(_filtered_df)
        print(f"Transaction Analysis completed. Flagged cases: {len(_db.get_flagged_cases())}")
        global df_with_anomalies
        df_with_anomalies = ad_agent.analyze(_filtered_df)
        print(f"Anomaly Detection completed. Anomalies: {df_with_anomalies['is_anomaly'].sum()}")
        print(f"df_with_anomalies columns: {df_with_anomalies.columns.tolist()}")
        inv_agent.investigate()
        max_emails = 10
        email_count = 0
        processed_txs = set()
        flagged_cases = _db.get_flagged_cases()
        print(f"Flagged cases structure: {flagged_cases.columns.tolist()}")
        for case in flagged_cases.itertuples():
            tx_id = case.id if 'id' in flagged_cases.columns else case.Index
            if tx_id not in processed_txs and email_count < max_emails:
                processed_txs.add(tx_id)
                rr_agent.generate_reports([flagged_cases.loc[case.Index]])
                email_count += 1
        print(f"Generated {email_count} SAR emails (limited to {max_emails})")
    except Exception as e:
        st.error(f"Error running agents: {str(e)}")

# Run agents
run_agents(db, filtered_df)

# Overview Page
if page == "Overview":
    st.header("Dashboard Overview")
    st.write(f"Total Transactions: {len(filtered_df)}")
    st.write(f"Flagged Anomalies: {df_with_anomalies['is_anomaly'].sum() if 'is_anomaly' in df_with_anomalies.columns else 0}")
    st.write(f"Flagged Cases: {len(db.get_flagged_cases())}")

# Transaction Network Page
elif page == "Transaction Network":
    st.header("Transaction Network Analysis")
    try:
        if filtered_df.empty:
            st.write("No data to display in the current filter.")
        else:
            G = nx.DiGraph()
            for _, row in filtered_df.iterrows():
                G.add_edge(row['nameOrig'], row['nameDest'], amount=row['amount'])
            if G.number_of_edges() > 0:
                pos = nx.spring_layout(G)
                plt.figure(figsize=(10, 6))
                nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=500, alpha=0.8)
                nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True)
                edge_labels = nx.get_edge_attributes(G, 'amount')
                nx.draw_networkx_edge_labels(G, pos, edge_labels={k: f"${v:.2f}" for k, v in edge_labels.items()})
                plt.title("Transaction Network Graph")
                st.pyplot(plt)
            else:
                st.write("No edges to display in the current filter.")
    except Exception as e:
        st.error(f"Error in transaction network graph: {str(e)}")

# Anomaly Detection Page
elif page == "Anomaly Detection":
    st.header("Anomaly Detection Analysis")
    try:
        if 'is_anomaly' not in df_with_anomalies.columns or df_with_anomalies.empty:
            st.write("No anomaly data to display.")
        else:
            fig = px.scatter(df_with_anomalies, x="amount", y="anomaly_score", color="is_anomaly",
                            color_discrete_map={0: "blue", 1: "red"},
                            title="Anomaly Score vs. Transaction Amount",
                            labels={"amount": "Transaction Amount ($)", "anomaly_score": "Anomaly Score"})
            fig.update_traces(marker=dict(size=8))
            st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Error in scatter plot: {str(e)}")

    # Network graph of anomalies
    st.subheader("Anomaly Transaction Network")
    try:
        anomalous_df = df_with_anomalies[df_with_anomalies['is_anomaly'] == 1]
        if anomalous_df.empty:
            st.write("No anomalous transactions to display.")
        else:
            G_anomaly = nx.DiGraph()
            for _, row in anomalous_df.iterrows():
                G_anomaly.add_edge(row['nameOrig'], row['nameDest'], amount=row['amount'], score=row['anomaly_score'])
            if G_anomaly.number_of_edges() > 0:
                pos = nx.spring_layout(G_anomaly)
                plt.figure(figsize=(10, 6))
                nx.draw_networkx_nodes(G_anomaly, pos, node_color='red', node_size=500, alpha=0.8)
                nx.draw_networkx_edges(G_anomaly, pos, edge_color='darkred', arrows=True)
                edge_labels = nx.get_edge_attributes(G_anomaly, 'amount')
                nx.draw_networkx_edge_labels(G_anomaly, pos, edge_labels={k: f"${v:.2f}" for k, v in edge_labels.items()})
                plt.title("Network of Anomalous Transactions")
                st.pyplot(plt)
            else:
                st.write("No edges in anomalous transactions.")
    except Exception as e:
        st.error(f"Error in network graph: {str(e)}")

# Investigation Summary Page
elif page == "Investigation Summary":
    st.header("Investigation Case Summary")
    try:
        flagged_cases = db.get_flagged_cases()
        if flagged_cases.empty or 'agent_type' not in flagged_cases.columns:
            st.write("No flagged cases or agent types to display.")
        else:
            case_counts = flagged_cases['agent_type'].value_counts()
            fig, ax = plt.subplots(figsize=(8, 5))
            case_counts.plot(kind='bar', ax=ax, color=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99'])
            ax.set_title("Flagged Cases by Agent Type")
            ax.set_xlabel("Agent Type")
            ax.set_ylabel("Number of Cases")
            st.pyplot(fig)
    except Exception as e:
        st.error(f"Error in investigation summary graph: {str(e)}")

# Regulatory Reporting Page
elif page == "Regulatory Reporting":
    st.header("Regulatory Reporting Status")
    try:
        sar_status = {"Delivered": 80, "Failed": 20}
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(sar_status.values(), labels=sar_status.keys(), autopct='%1.1f%%', colors=['#66B2FF', '#FF9999'])
        ax.set_title("SAR Delivery Status")
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error in regulatory reporting graph: {str(e)}")