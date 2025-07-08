import streamlit as st
import requests
from utils import apply_sidebar_style

apply_sidebar_style()
st.set_page_config(page_title="Power BI Governance Dashboard", layout="wide", page_icon="📊")
st.title("📊 Power BI Governance Dashboard")

# 🌐 Helper Functions
def reset_session():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def refresh_activity_data():
    for key in list(st.session_state.keys()):
        if key.startswith("uploaded_file") or key.endswith("_df") or key in ["data_processed", "file_just_uploaded"]:
            del st.session_state[key]

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

# 🔐 Login Flow
if not st.session_state.get("logged_in"):
    st.subheader("🔐 Authentication Required")
    with st.form("login_form"):
        access_token = st.text_input("Access Token", type="password")
        user_email = st.text_input("Your Email Address")
        submitted = st.form_submit_button("Authenticate")

        if submitted:
            if not access_token or not user_email:
                st.warning("⚠️ Please provide both access token and email.")
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
                    st.session_state.workspace_name = "-- Select a Workspace --"
                    st.session_state.workspace_id = None
                    st.rerun()
                else:
                    st.error("❌ No workspaces found for this email.")
else:
    # 🚪 Logout
    with st.sidebar:
        if st.button("🚪 Logout"):
            reset_session()
            st.rerun()

    st.subheader(f"✅ Logged in as {st.session_state.user_email}")
    workspace_options = st.session_state.get("workspace_options", {})
    current_ws_name = st.session_state.get("workspace_name", "-- Select a Workspace --")

    workspace_names = ["-- Select a Workspace --"] + list(workspace_options.keys())
    default_index = workspace_names.index(current_ws_name) if current_ws_name in workspace_names else 0
    selected_name = st.selectbox("Choose Workspace", workspace_names, index=default_index)

    # ✅ Refresh activity data if workspace changed
    if selected_name != "-- Select a Workspace --" and selected_name != current_ws_name:
        st.session_state.workspace_name = selected_name
        st.session_state.workspace_id = workspace_options[selected_name]
        refresh_activity_data()  # ⬅️ Clear uploaded file and cache
        st.rerun()

    if st.session_state.get("workspace_id"):
        st.success(f"Workspace selected: **{st.session_state.workspace_name}**")
        st.markdown("Use the sidebar to navigate to **Reports**, **Datasets**, **Users**, or **Activity Analysis**.")
    else:
        st.warning("⚠️ Please select a workspace to proceed.")

# 🎨 Button Styling
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
