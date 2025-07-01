# --- 0_Home.py ---
import streamlit as st
import requests

st.set_page_config(page_title="Power BI Workspace Overview", layout="wide")
st.title("📊 Power BI Governance Dashboard")

# Workspace options (replace with actual names and IDs from API if needed)
workspace_options = {
    "Sales Team Workspace": "1b602ded-5fca-42ed-a4fc-583fdac83a64",
    "Marketing Workspace": "2a8c5e12-5b4b-4d13-824c-2c963f4dc2ff",
    "Finance Workspace": "3d6f3411-6a33-4abc-91d0-8d8f7fe0e1aa"
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

