import streamlit as st
import requests
from utils import apply_sidebar_style

# Sidebar Styling
apply_sidebar_style()

# Page Settings
st.set_page_config(page_title="Power BI Governance Dashboard", layout="wide", page_icon="📊")
st.title("📊 Power BI Governance Dashboard")

# Session Reset Function
def reset_session():
    for key in ["access_token", "user_email", "workspace_ids", "workspace_names", "logged_in", "workspace_options"]:
        st.session_state.pop(key, None)

# API Calls
def get_all_workspaces(access_token):
    url = "https://api.powerbi.com/v1.0/myorg/groups"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.json().get("value", []) if response.status_code == 200 else []

def get_users_in_workspace(workspace_id, access_token):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return [u.get("emailAddress", "") for u in response.json().get("value", [])] if response.status_code == 200 else []

# Login Form
if not st.session_state.get("logged_in"):
    st.subheader("🔐 Authentication Required")
    with st.form("login_form"):
        access_token = st.text_input("Access Token", type="password")
        user_email = st.text_input("Your Email Address")
        submitted = st.form_submit_button("Authenticate")

        if submitted:
            if not access_token or not user_email:
                st.warning("Please provide both access token and email.")
            else:
                workspaces = get_all_workspaces(access_token)
                matched = {
                    ws["name"]: ws["id"]
                    for ws in workspaces
                    if user_email in get_users_in_workspace(ws["id"], access_token)
                }
                if matched:
                    st.session_state.access_token = access_token
                    st.session_state.user_email = user_email
                    st.session_state.workspace_options = matched
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("No workspaces found for this email.")
else:
    # Logout Button
    with st.sidebar:
        if st.button("🚪 Logout"):
            reset_session()
            st.rerun()

    # Login Info
    st.subheader(f"✅ Logged in as {st.session_state.user_email}")
    workspace_options = st.session_state.get("workspace_options", {})

    # Multi-select Workspace
    selected_names = st.multiselect(
        "Choose Workspaces",
        options=list(workspace_options.keys()),
        default=st.session_state.get("workspace_names", [])
    )

    if selected_names:
        st.session_state.workspace_names = selected_names
        st.session_state.workspace_ids = [workspace_options[name] for name in selected_names]
        st.success(f"Workspaces selected: {', '.join(selected_names)}")
        st.markdown("Use the sidebar to navigate to **Reports**, **Datasets**, **Users**, or **Activity Analysis** for the selected workspaces.")
    else:
        st.warning("⚠️ Please select at least one workspace to proceed.")
        st.session_state.workspace_names = []
        st.session_state.workspace_ids = []

# Button Hover Styling
st.markdown("""
<style>
.stFormSubmitButton>button:hover {
    background-color: green;
    color: white;
}
.stButton>button:hover {
    background-color: darkred;
    color: white;
}
</style>
""", unsafe_allow_html=True)
