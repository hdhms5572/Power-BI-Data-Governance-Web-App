import streamlit as st
import requests

st.set_page_config(page_title="Power BI Governance Dashboard", layout="wide", page_icon="📊")

# ------------------ Helper Functions ------------------
def reset_session():
    for key in ["access_token", "user_email", "workspace_id", "workspace_name", "logged_in", "workspace_options"]:
        st.session_state.pop(key, None)

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

# ------------------ Sidebar Styling ------------------
st.markdown("""
<style>
/* Sidebar container */
[data-testid="stSidebar"] {
    background-color: #fdfefe;
    padding: 1.5rem 1rem;
    border-right: 1px solid #e1e4e8;
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

/* Improve sidebar link fonts (auto-generated nav links) */
[data-testid="stSidebar"] ul {
    padding-left: 0;
}
[data-testid="stSidebar"] ul li a {
    font-size: 1.05rem !important;
    font-weight: 600;
    color: #1f2937 !important;
    padding: 0.5rem 0;
    margin-bottom: 0.4rem;
    border-radius: 6px;
    display: block;
    text-decoration: none;
}
[data-testid="stSidebar"] ul li a:hover {
    background-color: #eef2f7;
    color: #0f172a !important;
}

/* Sidebar info text (email, workspace) */
.sidebar-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #2d3436;
    margin-top: 0.5rem;
    margin-bottom: 0.7rem;
}

/* Button improvements */
.stButton>button {
    background-color: #e74c3c;
    color: white;
    border-radius: 8px;
    padding: 0.45rem 1.2rem;
    font-weight: 600;
    font-size: 0.95rem;
}
.stButton>button:hover {
    background-color: #c0392b;
    color: white;
}
</style>
""", unsafe_allow_html=True)



# ------------------ Header ------------------
st.title("📊 Power BI Governance Dashboard")

# ------------------ Login ------------------
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
                    # set default workspace
                    first_key = next(iter(matched))
                    st.session_state.workspace_name = first_key
                    st.session_state.workspace_id = matched[first_key]
                    st.rerun()
                else:
                    st.error("No workspaces found for this email.")
else:
    # ------------------ Sidebar (Logout Only) ------------------
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🧭 Options</div>', unsafe_allow_html=True)
        if st.button("🚪 Logout"):
            reset_session()
            st.rerun()


    # ------------------ Main Page: Workspace Selection ------------------
    
    # ------------------ Main Page: Workspace Selection ------------------
    st.subheader(f"✅ Logged in as {st.session_state.user_email}")

    workspace_options = st.session_state.get("workspace_options", {})

    # User must explicitly select
    selected_name = st.selectbox("Choose Workspace", ["-- Select a Workspace --"] + list(workspace_options.keys()))

    if selected_name == "-- Select a Workspace --":
        st.warning("⚠️ Please select a workspace to proceed.")
        st.session_state.workspace_id = None
        st.session_state.workspace_name = None
    else:
        if selected_name != st.session_state.get("workspace_name"):
            st.session_state.workspace_name = selected_name
            st.session_state.workspace_id = workspace_options[selected_name]
            st.rerun()

    if st.session_state.get("workspace_id"):
        st.success(f"Workspace selected: **{st.session_state.workspace_name}**")
        st.markdown("Use the sidebar to navigate to **Reports**, **Datasets**, **Users**, or **Activity Analysis**.")

