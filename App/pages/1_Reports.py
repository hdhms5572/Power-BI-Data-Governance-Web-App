import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import call_powerbi_api, get_filtered_dataframes  # Shared logic

st.title("📄 Reports")

# Check for required session state values
if not (st.session_state.get("access_token") and st.session_state.get("workspace_id") and st.session_state.get("user_email")):
    st.warning("❌ Missing access token, workspace ID, or email. Please provide credentials in the main page.")
    st.stop()

# Retrieve from session state
token = st.session_state.access_token
workspace = st.session_state.workspace_id
email = st.session_state.user_email

# Fetch data
reports_df, datasets_df, users_df = get_filtered_dataframes(token, workspace, email)

if reports_df.empty:
    st.warning("📭 No report data available or failed to load.")
    st.stop()

st.dataframe(reports_df)
col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Report Status Count")
    fig1, ax1 = plt.subplots()
    sns.countplot(data=reports_df, x="reportstatus", palette={"Active": "green", "Inactive": "red", "Active (Outdated)": "orange"}, ax=ax1)
    st.pyplot(fig1)
with col2:
    st.subheader("🥧 Report Status Share")
    fig2, ax2 = plt.subplots()
    counts = reports_df["reportstatus"].value_counts()
    ax2.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=["green", "red", "orange"], startangle=150)
    ax2.axis("equal")
    st.pyplot(fig2)
