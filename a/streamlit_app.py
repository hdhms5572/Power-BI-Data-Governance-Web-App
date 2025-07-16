import streamlit as st
import requests
from utils import apply_sidebar_style, get_base64_image
from utils import theme_selector, set_theme
from utils import render_user_profile




st.set_page_config(page_title="Power BI Governance Dashboard", layout="wide", page_icon="📊")
def inject_external_style():
    with open("./static/style.css") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

apply_sidebar_style()
inject_external_style()


 
render_user_profile()
mode = theme_selector()  
set_theme(mode)              



logo_base64 = get_base64_image("static/dover_logo.png")  # use relative path from the app root

st.markdown(f"""
    <div style='display: flex; align-items: center; justify-content: center; gap: 20px;'>
        <img src='data:image/png;base64,{logo_base64}' width='80'>
        <h1 style='text-align: center;'>📊 Power BI Governance Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

# Reset session state
def reset_session():
    for key in ["access_token", "user_email", "workspace_ids", "workspace_names", "logged_in", "workspace_options"]:
        st.session_state.pop(key, None)

# Get all workspaces from Power BI API
def get_all_workspaces(access_token):
    url = "https://api.powerbi.com/v1.0/myorg/groups"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.json().get("value", []) if response.status_code == 200 else []

# Get users in workspace from Power BI API
def get_users_in_workspace(workspace_id, access_token):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return [u.get("emailAddress", "") for u in response.json().get("value", [])] if response.status_code == 200 else []

# Authentication section
if not st.session_state.get("logged_in"):
    with st.container():
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
    # Sidebar logout button
    with st.sidebar:
        if st.button("🚪 Logout"):
            reset_session()
            st.rerun()

    # Workspace selection
    st.subheader(f"✅ Logged in as {st.session_state.user_email}")
    workspace_options = st.session_state.get("workspace_options", {})
    st.markdown("---")

    select_all = st.checkbox("Select All Workspaces")
    workspace_names = list(workspace_options.keys())
    default_selection = workspace_names if select_all else st.session_state.get("workspace_names", [])

    selected_names = st.multiselect(
        "Choose Workspaces",
        options=workspace_names,
        default=default_selection
    )

    if selected_names:
        st.session_state.workspace_names = selected_names
        st.session_state.workspace_ids = [workspace_options[name] for name in selected_names]
        st.success(f"Workspaces selected: {', '.join(selected_names)}")
        st.markdown("🔍 Use the sidebar to explore **Reports**, **Datasets**, **Users**, or **Activity Analysis**.")
    else:
        st.warning("⚠️ Please select at least one workspace to proceed.")
        st.session_state.workspace_names = []
        st.session_state.workspace_ids = []
