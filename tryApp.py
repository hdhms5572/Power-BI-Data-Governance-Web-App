import streamlit as st
import requests
import pandas as pd

# Sidebar Inputs
st.sidebar.title("Power BI API Settings")
access_token = st.sidebar.text_input("Access Token", type="password")
workspace_id = st.sidebar.text_input("Workspace ID", value="d459e975-fd2e-4db5-a602-03f515215de2")

# Dummy function to map users to company (You can replace with actual mapping logic)
def get_user_company(email):
    company_map = {
        "user1@abc.com": "ABC Corp",
        "user2@xyz.com": "XYZ Ltd",
        "admin@global.com": "Global Admin"
    }
    return company_map.get(email.lower(), None)

# Power BI API Call
def call_powerbi_api(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API call failed: {response.status_code} - {response.text}")
        return None

# Start processing if token is provided
if access_token and workspace_id:
    reports_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
    datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    users_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"

    reports_data = call_powerbi_api(reports_url, access_token)
    datasets_data = call_powerbi_api(datasets_url, access_token)
    users_data = call_powerbi_api(users_url, access_token)

    if reports_data and datasets_data and users_data:
        reports_df = pd.DataFrame(reports_data["value"])
        datasets_df = pd.DataFrame(datasets_data["value"])
        users_df = pd.DataFrame(users_data["value"])

        st.title("Power BI Workspace Overview")

        # --- 👤 Login User Selection for Demo Purpose ---
        user_email = st.selectbox("Select User", users_df['emailAddress'].unique())
        user_company = get_user_company(user_email)

        if user_company:
            st.success(f"Access granted for: {user_email} ({user_company})")

            # --- 🔐 Apply RLS Filter Based on Company ---
            # For demo, assume dataset/report names contain company name
            filtered_reports_df = reports_df[reports_df['name'].str.contains(user_company, case=False)]
            filtered_datasets_df = datasets_df[datasets_df['name'].str.contains(user_company, case=False)]

            st.subheader("📄 Reports (Company Restricted)")
            st.write(filtered_reports_df)

            st.subheader("📊 Datasets (Company Restricted)")
            st.write(filtered_datasets_df)

            st.subheader("👥 All Workspace Users")
            st.write(users_df)
        else:
            st.error("This user has no company mapping. Access Denied.")
    else:
        st.warning("Could not fetch all data. Please check your token and workspace ID.")
else:
    st.info("Enter your access token and workspace ID in the sidebar to begin.")
