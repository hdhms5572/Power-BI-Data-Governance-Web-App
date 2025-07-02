import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import call_powerbi_api, get_filtered_dataframes,show_reports_table
from utils import apply_sidebar_style
apply_sidebar_style()
from utils import show_workspace_header
show_workspace_header()


st.title("📊 Datasets")

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

if datasets_df.empty:
    st.warning("📭 No dataset data available or failed to load.")
    st.stop()

show_reports_table(datasets_df)
col1, col2 = st.columns(2)
with col1:
    st.subheader("📓 Dataset Status vs Freshness")
    group = datasets_df.groupby(["datasetStatus", "outdated"]).size().unstack(fill_value=0)
    fig3, ax3 = plt.subplots()
    group.plot(kind="bar", stacked=True, ax=ax3, colormap="coolwarm")
    st.pyplot(fig3)
with col2:
    st.subheader("🌡️ Heatmap: Report vs Dataset Status")
    cross = pd.crosstab(reports_df["reportstatus"], reports_df["datasetStatus"])
    fig4, ax4 = plt.subplots()
    sns.heatmap(cross, annot=True, fmt="d", cmap="Blues", ax=ax4)
    st.pyplot(fig4)
