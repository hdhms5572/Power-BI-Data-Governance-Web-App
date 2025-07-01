# main.py
import streamlit as st
from modules.api import fetch_reports, fetch_datasets, fetch_users
from modules.utils import filter_data, classify_report, classify_artifact_type
from modules.visuals import render_reports_page, render_datasets_page, render_users_page, render_activity_page

st.set_page_config(page_title="Power BI Workspace Overview", layout="wide")

# Sidebar
st.sidebar.title("🔐 Power BI API Settings")
access_token = st.sidebar.text_input("Access Token", type="password", help="Enter your Power BI access token")
workspace_id = st.sidebar.text_input("Workspace ID", help="Enter your workspace ID")
user_email = st.sidebar.text_input("Your Email Address", help="Used for access control")

page = st.selectbox("Select a page", ("Reports", "Datasets", "Users", "Activity Analysis"), index=None, placeholder="Choose view")

if access_token and workspace_id and user_email:
    with st.spinner("Fetching data..."):
        reports_data = fetch_reports(access_token, workspace_id)
        datasets_data = fetch_datasets(access_token, workspace_id)
        users_data = fetch_users(access_token, workspace_id)

    if reports_data and datasets_data and users_data:
        domain = user_email.split('@')[-1]
        filtered_reports_df, filtered_datasets_df, filtered_users_df = filter_data(reports_data, datasets_data, users_data, domain)

        if page == "Reports":
            render_reports_page(filtered_reports_df)

        elif page == "Datasets":
            render_datasets_page(filtered_datasets_df, filtered_reports_df)

        elif page == "Users":
            render_users_page(filtered_users_df)

        elif page == "Activity Analysis":
            render_activity_page(filtered_users_df, filtered_datasets_df, filtered_reports_df, domain)
    else:
        st.error("❌ Could not fetch all data. Check token or workspace ID.")
else:
    st.info("🔑 Enter credentials in the sidebar to begin.")
