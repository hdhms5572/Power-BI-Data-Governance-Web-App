import requests
import pandas as pd
import streamlit as st

def validate_session():
    if not (st.session_state.get("access_token") and st.session_state.get("workspace_id") and st.session_state.get("user_email")):
        st.warning("❌ Missing access token, workspace ID, or email. Please provide credentials in the main page.")
        st.stop()

# utils.py
def show_workspace():
    name = st.session_state.get("workspace_name")
    if name:
        st.sidebar.markdown(f"### 📁 Current Workspace: **{name}**")
    else:
        st.warning("⚠️ No workspace selected.")
        st.stop()

# utils.py
def apply_sidebar_style():
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: lightblack;
            padding: 1.5rem 1rem;
            border-right: 1px solid gray;
            font-family: 'Segoe UI', 'Inter', sans-serif;
        }
        [data-testid="stSidebar"] ul {
            padding-left: 0;
        }
        [data-testid="stSidebar"] ul li a {
            font-size: 1.05rem !important;
            font-weight: 600;
            color: white !important;
            padding: 0.5rem 0;
            margin-bottom: 0.4rem;
            border-radius: 6px;
            display: block;
            text-decoration: none;
        }
        [data-testid="stSidebar"] ul li a:hover {
            background-color: lightblack !important;
        }
    </style>
    """, unsafe_allow_html=True)

    
def call_powerbi_api(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API call failed: {response.status_code} - {response.text}")
        return None

def get_filtered_dataframes(token, workspace_id, user_email):
    # URLs
    reports_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
    datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    users_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"

    reports_data = call_powerbi_api(reports_url, token)
    datasets_data = call_powerbi_api(datasets_url, token)
    users_data = call_powerbi_api(users_url, token)

    if not (reports_data and datasets_data and users_data):
        st.error("Failed to fetch data from API.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    reports_df = pd.DataFrame(reports_data["value"])
    datasets_df = pd.DataFrame(datasets_data["value"])
    users_df = pd.DataFrame(users_data["value"])

    users_df.drop(columns=['identifier'], errors='ignore', inplace=True)
    users_df.dropna(subset=['emailAddress'], inplace=True)

    datasets_df["createdDate"] = pd.to_datetime(datasets_df["createdDate"], errors="coerce").dt.tz_localize(None)
    cutoff = pd.Timestamp.now() - pd.DateOffset(months=12)
    datasets_df["outdated"] = datasets_df["createdDate"] < cutoff
    datasets_df["datasetStatus"] = datasets_df["isRefreshable"].apply(lambda x: "Active" if x else "Inactive")

    reports_df = reports_df.merge(
        datasets_df[['id', 'datasetStatus', 'outdated']],
        left_on="datasetId",
        right_on="id",
        how="left"
    )

    reports_df.drop(columns=['id_y','users','subscriptions'], inplace=True, errors='ignore')
    reports_df.rename(columns={"id_x":"id"}, inplace=True)
    datasets_df.drop(columns=["upstreamDatasets","users"], inplace=True, errors='ignore')

    def classify_report(row):
        if row['datasetStatus'] == "Inactive":
            return "Inactive"
        elif row['datasetStatus'] == "Active" and row["outdated"]:
            return 'Active (Outdated)'
        elif row['datasetStatus'] == "Active":
            return 'Active'
        return 'Unknown'

    reports_df["Reportstatus Based on Dataset"] = reports_df.apply(classify_report, axis=1)

    return reports_df, datasets_df, users_df
