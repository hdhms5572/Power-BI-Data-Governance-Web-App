import streamlit as st
import requests

st.set_page_config(page_title="Power BI Workspace Overview", layout="wide")
st.title("📊 Power BI Governance Dashboard")

st.sidebar.title("🔐 Power BI API Settings")
st.session_state.access_token = st.sidebar.text_input("Access Token", type="password")
st.session_state.user_email = st.sidebar.text_input("Your Email Address")


# Only proceed if access token and email are provided
if not (st.session_state.access_token and st.session_state.user_email):
    st.warning("🔑 Please enter your access token and email address to load available workspaces.")
    st.stop()

# Function to get all workspaces
def get_all_workspaces(access_token):
    url = "https://api.powerbi.com/v1.0/myorg/groups"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        st.error(f"Failed to fetch workspaces: {response.status_code}")
        return []
    
all_workspaces = get_all_workspaces(st.session_state.access_token)

workspace_options = {workspace["name"]: workspace["id"] for workspace in all_workspaces}

# Function to get users in a workspace
def get_users_in_workspace(workspace_id, access_token):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
    headers = {"Authorization": f"Bearer {access_token}"}
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

st.success("✅ Credentials and matching workspace loaded. Use the sidebar to navigate between pages.")