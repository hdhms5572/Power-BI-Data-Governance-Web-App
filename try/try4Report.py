import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes

st.title("📄 Reports")

# Credential check
if not (st.session_state.get("access_token") and st.session_state.get("workspace_id") and st.session_state.get("user_email")):
    st.warning("❌ Missing access token, workspace ID, or email. Please provide credentials in the main page.")
    st.stop()

token = st.session_state.access_token
workspace = st.session_state.workspace_id
email = st.session_state.user_email

reports_df, datasets_df, users_df = get_filtered_dataframes(token, workspace, email)

if reports_df.empty:
    st.warning("📭 No report data available or failed to load.")
    st.stop()

# Initialize selected dataset state if not set
if "selected_dataset_id" not in st.session_state:
    st.session_state.selected_dataset_id = None

# --- Report Table with 'View Dataset' Buttons Inline ---
st.markdown("### 🔗 Report Table")
for index, row in reports_df.iterrows():
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 3, 2])
        col1.markdown(f"**{row['name']}**")
        col2.markdown(f"`{row['datasetId']}`")
        col3.markdown(f"{row.get('reportstatus', 'Unknown')}")
        col4.write("")  # Placeholder for future use

        if col5.button("View Dataset", key=f"btn_{row['datasetId']}"):
            st.session_state.selected_dataset_id = row['datasetId'] if st.session_state.selected_dataset_id != row['datasetId'] else None

        if st.session_state.selected_dataset_id == row['datasetId']:
            selected_dataset = datasets_df[datasets_df["id"] == row["datasetId"]]
            if not selected_dataset.empty:
                st.markdown(f"##### 📌 Dataset for ID: `{row['datasetId']}`")
                st.dataframe(selected_dataset, use_container_width=True)
            else:
                st.info("⚠️ No dataset found for this report.")

# --- Charts ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Report Status Count")
    fig1, ax1 = plt.subplots()
    sns.countplot(data=reports_df, x="reportstatus",
                  palette={"Active": "green", "Inactive": "red", "Active (Outdated)": "orange"}, ax=ax1)
    st.pyplot(fig1)

with col2:
    st.subheader("🥧 Report Status Share")
    fig2, ax2 = plt.subplots()
    counts = reports_df["reportstatus"].value_counts()
    ax2.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=["green", "red", "orange"], startangle=150)
    ax2.axis("equal")
    st.pyplot(fig2)
