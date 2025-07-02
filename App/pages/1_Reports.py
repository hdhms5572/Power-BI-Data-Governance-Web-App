import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import call_powerbi_api, get_filtered_dataframes

st.markdown("<h1 style='text-align: center;'>📄 Reports</h1>", unsafe_allow_html=True)
st.markdown("""<hr>""", unsafe_allow_html=True)

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

col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Report Status Count")
    fig, ax = plt.subplots()
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_alpha(0.01)
    ax.patch.set_alpha(0.01)   
    ax.title.set_color('white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.tick_params(colors='white')
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color('white')
    sns.countplot(data=reports_df, x="reportstatus", palette={"Active": "green", "Inactive": "red", "Active (Outdated)": "orange"}, ax=ax)
    st.pyplot(fig)
with col2:
    st.subheader("🥧 Report Status Share")
    counts = reports_df["reportstatus"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_alpha(0.01)
    ax.patch.set_alpha(0.01)
    ax.title.set_color('white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white') 
    ax.tick_params(colors='white')
    wedges, texts, autotexts = ax.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=["green", "red", "orange"], startangle=150,)
    for text in texts:
        text.set_color('white')
        text.set_fontweight('bold')
    ax.axis("equal")
    ax.set_title("Report Status Distribution", color='white')

    st.pyplot(fig)

st.dataframe(reports_df)
