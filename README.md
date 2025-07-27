# Antimoneylaundering

AML Investigation Platform
Overview
The AML Investigation Platform is an AI-powered tool designed to detect fraudulent transactions and generate Suspicious Activity Reports (SARs) for anti-money laundering (AML) compliance. Built using Python, this platform leverages a modular agent-based architecture to analyze transaction data, identify anomalies, investigate flagged cases, and provide regulatory reporting. The system includes an interactive Streamlit dashboard for visualization and monitoring, processing up to 10,000 transaction samples from the PaySim synthetic dataset.

This project aims to streamline AML processes, reduce manual effort, and enhance financial security by providing actionable insights through visualizations and automated reporting.

Features
Transaction Analysis: Flags suspicious transactions based on predefined rules.
Anomaly Detection: Identifies outliers using statistical methods.
Investigation: Generates detailed SARs for flagged cases.
Regulatory Reporting: Saves and attempts to email SARs (limited by SMTP constraints).
Interactive Dashboard: Offers pages for Overview, Transaction Network, Anomaly Detection, Investigation Summary, and Regulatory Reporting.
Data Management: Stores and queries data using SQLite database.
Scalability: Supports 10,000-row datasets with potential for expansion.
Installation
Prerequisites
Python 3.8 or higher
Git (for cloning the repository)
Required Python libraries (install via requirements.txt
Dataset Link: https://www.kaggle.com/datasets/ealaxi/paysim1
