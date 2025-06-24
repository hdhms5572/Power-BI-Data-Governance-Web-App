
import streamlit as st
import requests
import pandas as pd

# Input fields in the Streamlit sidebar
st.sidebar.title("Power BI API Settings")
access_token = st.sidebar.text_input("Access Token", type="password")
workspace_id = st.sidebar.text_input("Workspace ID", value="d459e975-fd2e-4db5-a602-03f515215de2")
user_email = st.sidebar.text_input("Your Email Address") 

# API call function
def call_powerbi_api(url, token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API call failed: {response.status_code} - {response.text}")
        return None

# Main logic
if access_token and workspace_id and user_email:
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

        # Extract domain from logged-in user's email
        domain = user_email.split('@')[-1]

        # Apply RLS: Filter datasets by domain of configuredBy
        filtered_datasets_df = datasets_df[datasets_df["configuredBy"].str.endswith(domain, na=False)]

        # Get dataset IDs user is allowed to see
        allowed_dataset_ids = filtered_datasets_df["id"].tolist()

        # Filter reports whose datasetId is in allowed list
        filtered_reports_df = reports_df[reports_df["datasetId"].isin(allowed_dataset_ids)]

        # Filter users from same domain
        if "emailAddress" in users_df.columns:
            filtered_users_df = users_df[users_df["emailAddress"].str.endswith(domain, na=False)]
        else:
            filtered_users_df = users_df  # fallback if column missing

        # Display filtered data
        st.title("🔒 Power BI Workspace (Filtered by Domain)")

        st.subheader("📄 Reports")
        st.write(filtered_reports_df)

        st.subheader("📊 Datasets")
        st.write(filtered_datasets_df)

        st.subheader("👥 Users")
        st.write(filtered_users_df)
    else:
        st.warning("Could not fetch all data. Please check your token and workspace ID.")
else:
    st.info("Enter your access token, email, and workspace ID in the sidebar to begin.")
