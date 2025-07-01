import streamlit as st
import requests

st.set_page_config(page_title="Power BI Workspace Overview", layout="wide")
st.title("📊 Power BI Governance Dashboard")

# Workspace options (replace with actual names and IDs from API if needed)
workspace_options = {
    "D&A Data Governance": "cf7a33dd-365c-465d-b3a6-89cd2a3ef08c",
    "D&A SCDP": "dc5090e8-0007-4391-9ce4-2966879e575e",
    "D&A SQDIP - DEV": "d459e975-fd2e-4db5-a602-03f515215de2",
    "D&A TEST   ": "1b602ded-5fca-42ed-a4fc-583fdac83a64",
    "Maag-BI-Dev": "371cc649-ec08-4e28-abd7-535945fd401d",
    "OPW_BI_REPORTING_UAT": "023c2768-9f9d-4b5d-b360-548df84ec240",
    "PSG HYDRO UAT": "f5e057fd-df7b-4ea0-b9f8-d8fda3e4aafe"
}

st.sidebar.title("🔐 Power BI API Settings")
st.session_state.access_token = st.sidebar.text_input("Access Token", type="password")
st.session_state.user_email = st.sidebar.text_input("Your Email Address")

# Only proceed if access token and email are provided
if not (st.session_state.access_token and st.session_state.user_email):
    st.warning("🔑 Please enter your access token and email address to load available workspaces.")
    st.stop()

# Function to get users in a workspace
def get_users_in_workspace(workspace_id, token):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [user.get("emailAddress", "") for user in response.json().get("value", [])]
    return []

# Filter workspaces containing the user's email
available_workspaces = {
    name: wid for name, wid in workspace_options.items()
    if st.session_state.user_email in get_users_in_workspace(wid, st.session_state.access_token)
}

if not available_workspaces:
    st.warning("❌ No workspaces found for this email address.")
    st.stop()

selected_workspace_name = st.sidebar.selectbox("Select Workspace", list(available_workspaces.keys()))
st.session_state.workspace_id = available_workspaces[selected_workspace_name]

# Show selected workspace ID
st.sidebar.markdown(f"**Workspace ID:** `{st.session_state.workspace_id}`")
st.success("✅ Credentials and matching workspace loaded. Use the sidebar to navigate between pages.")
