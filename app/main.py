# aml_investigation_platform/app/main.py

import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from db.sqlite_db import AMLDatabase
from agents.transaction_analysis import TransactionAnalysisAgent
from agents.anomaly_detection import AnomalyDetectionAgent
from agents.investigation import InvestigationAgent

st.set_page_config(page_title="AML Dashboard", layout="wide")
st.title("💼 AML Investigation Platform")

# Initialize DB + agents
db = AMLDatabase()
investigation_agent = InvestigationAgent()

@st.cache_data
def load_data():
    from utils.data_loader import load_paysim_data
    df = load_paysim_data()
    df = df.sample(10000, random_state=42).reset_index(drop=True)
    df = df.reset_index().rename(columns={"index": "id"})
    db.insert_transactions(df)
    return df

df = load_data()

# Session state flags
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

# Layout Tabs
tabs = st.tabs(["📊 Overview", "🕸️ Transaction Network", "🚨 Flagged Cases"])

# ---------------------- OVERVIEW TAB -------------------------
with tabs[0]:
    st.subheader("🧠 Analysis Pipeline")

    if st.button("🚀 Run Analysis"):
        st.write("🔍 Running Transaction Analysis...")
        TransactionAnalysisAgent().analyze(df)
        st.write("📊 Running Anomaly Detection...")
        AnomalyDetectionAgent().analyze(df)
        st.session_state.analysis_done = True
        st.success("✅ Analysis Complete!")

    if st.session_state.analysis_done:
        st.info("✅ Data has been analyzed. Proceed to next tabs to review results.")
    else:
        st.warning("⚠️ Run analysis to enable anomaly detection and SAR generation.")

# ---------------------- NETWORK TAB --------------------------
with tabs[1]:
    st.subheader("🕸️ Transaction Network Graph")
    G = nx.DiGraph()
    for _, row in df.head(100).iterrows():
        G.add_edge(row['nameOrig'], row['nameDest'], amount=row['amount'])

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(G, pos, node_size=30, node_color='dodgerblue', alpha=0.7)
    nx.draw_networkx_edges(G, pos, alpha=0.5)
    plt.axis("off")
    st.pyplot(plt)

# ---------------------- FLAGGED CASES TAB ---------------------
with tabs[2]:
    st.subheader("🚨 Flagged Transactions & SAR Reports")

    flagged_df = db.get_flagged_cases()
    if not flagged_df.empty:
        st.write(f"🧾 Total Flagged Cases: {len(flagged_df)}")

        st.dataframe(flagged_df)

        if st.session_state.analysis_done:
            st.write("📄 Generating SAR Reports...")
            reports = investigation_agent.investigate()

            for tid in flagged_df['transaction_id'].unique():
                if tid in reports:
                    st.download_button(
                        label=f"⬇️ Download SAR for Transaction {tid}",
                        data=reports[tid],
                        file_name=f"sar_{tid}.txt",
                        mime="text/plain"
                    )
        else:
            st.error("❌ Run analysis before generating SARs.")
    else:
        st.info("ℹ️ No flagged cases available yet.")
