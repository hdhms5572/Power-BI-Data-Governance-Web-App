import streamlit as st
from utils import call_powerbi_api, get_filtered_dataframes

st.markdown("<h1 style='text-align: center;'>👥 Users</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

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

if users_df.empty:
    st.warning("📭 No user data available or failed to load.")
    st.stop()

# Display user data
st.dataframe(users_df[["displayName", "emailAddress", "groupUserAccessRight", "principalType"]])
