import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Streamlit config
st.set_page_config(page_title="Power BI Workspace Overview", layout="wide")

# Sidebar for credentials
st.sidebar.title("🔐 Power BI API Settings")
access_token = st.sidebar.text_input("Access Token", type="password")
workspace_id = st.sidebar.text_input("Workspace ID", value="1b602ded-5fca-42ed-a4fc-583fdac83a64")
#st.sidebar.header("📂 Upload Data Files")
#uploaded_activity = st.sidebar.file_uploader("Upload Activity Log", type=["csv", "xlsx"])

# API call function
def call_powerbi_api(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API call failed: {response.status_code} - {response.text}")
        return None

# Main logic
if access_token and workspace_id:
    # API endpoints
    reports_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
    datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    users_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"

    # Fetch data
    reports_data = call_powerbi_api(reports_url, access_token)
    datasets_data = call_powerbi_api(datasets_url, access_token)
    users_data = call_powerbi_api(users_url, access_token)

    if reports_data and datasets_data and users_data:
        # Create DataFrames
        reports_df = pd.DataFrame(reports_data["value"])
        datasets_df = pd.DataFrame(datasets_data["value"])
        users_df = pd.DataFrame(users_data["value"])

        # Data cleanup
        users_df = users_df.drop(columns=['identifier'], errors='ignore')
        users_df.dropna(subset=['emailAddress'], inplace=True)
        reports_df = reports_df.drop(columns=['subscriptions'], errors='ignore')
        datasets_df = datasets_df.drop(columns=['upstreamDatasets'], errors='ignore')

        # Dataset cleanup and classification
        datasets_df["createdDate"] = pd.to_datetime(datasets_df["createdDate"], errors="coerce").dt.tz_localize(None)
        cutoff = pd.Timestamp.now() - pd.DateOffset(months=12)
        datasets_df["outdated"] = datasets_df["createdDate"] < cutoff
        datasets_df["datasetStatus"] = datasets_df["isRefreshable"].apply(lambda x: "Active" if x else "Inactive")

        # Add dataset attributes to reports
        reports_df = reports_df.merge(
            datasets_df[['id', 'datasetStatus', 'outdated']],
            left_on="datasetId",
            right_on="id",
            how="left"
        )
        
        reports_df.drop(columns=["id_y"], inplace=True)
        reports_df.rename(columns={"id_x": "id"}, inplace=True)


        def classify_report(row):
            if row['datasetStatus'] == "Inactive":
                return "Inactive"
            elif row['datasetStatus'] == "Active" and row["outdated"]:
                return 'Active (Outdated)'
            elif row['datasetStatus'] == "Active" and not row["outdated"]:
                return 'Active'
            else:
                return 'Unknown'

        reports_df["reportstatus"] = reports_df.apply(classify_report, axis=1)

        # Title
        st.title("📊 Power BI Workspace Overview")

        # DataFrames
        st.subheader("📄 Reports")
        st.dataframe(reports_df)

        st.subheader("📊 Datasets")
        st.dataframe(datasets_df)

        st.subheader("👥 Users")
        st.dataframe(users_df)

        #if uploaded_activity:
        #activity_df = pd.read_csv(uploaded_activity) if uploaded_activity.name.endswith(".csv") else pd.read_excel(uploaded_activity)
        activity_df=pd.read_csv(r"C:\Users\10094790\Downloads\data.csv")
       
        st.dataframe(activity_df)

        #Sorting Based On Activity Time
        if "Activity time" in activity_df.columns:
            activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
            activity_df = activity_df.sort_values("Activity time")
            st.subheader("📋 Activity Log (Sorted by 'Activity time')")
        else:
            st.error("❌ 'Activity time' column not found. Please verify the file.")


        # Get only the most recent access per ArtifactId
        #Dropping Duplicate records based on Artifact ID
        #latest_access = activity_df.sort_values("Activity time").drop_duplicates(subset="ArtifactId", keep="last")
        # Display that table
       # st.subheader("📌 Most Recently Accessed Artifacts based on artifactid")
        #st.dataframe(latest_access)

        #Dropping Duplicate records based on Artifact Name
        latest_access1 = activity_df.sort_values("Activity time").drop_duplicates(subset="Artifact Name", keep="last")
        latest_access1.rename(columns={"Activity time": "Latest Activity"}, inplace=True)

       
        # Display that table
        st.subheader("📌 Most Recently Accessed Artifacts based on artifactName")
        st.dataframe(latest_access1)
        report_ids = set(reports_df["id"])
        dataset_ids = set(datasets_df["id"])
        
        #Classify Artifact Type based on its ID
        def classify_artifact_type(artifact_id):
            if artifact_id in report_ids:
                return "Report"
            elif artifact_id in dataset_ids:
                return "Dataset"
            else:
                return "Unknown"

        latest_access1["ArtifactType"] = latest_access1["ArtifactId"].apply(classify_artifact_type)

        # Merge report status where applicable
        
        latest_access1 = latest_access1.merge(
            reports_df[["id", "reportstatus"]],
            left_on="ArtifactId",
            right_on="id",
            how="left"
        ).rename(columns={"reportstatus": "ReportStatus"}).drop(columns=["id"])

        # Merge dataset status where applicable
        latest_access1 = latest_access1.merge(
            datasets_df[["id", "datasetStatus"]],
            left_on="ArtifactId",
            right_on="id",
            how="left"
        ).rename(columns={"datasetStatus": "DatasetStatus"}).drop(columns=["id"])

        def resolve_status(row):
            if row["ArtifactType"] == "Report":
                return row["ReportStatus"]
            elif row["ArtifactType"] == "Dataset":
                return row["DatasetStatus"]
            else:
                return "Unknown"

        latest_access1["ArtifactStatus"] = latest_access1.apply(resolve_status, axis=1)

        st.dataframe(latest_access1)
        

        active_user_emails = activity_df["User email"].dropna().unique()
        
        #Classifying Active Users
        users_df["activityStatus"] = users_df["emailAddress"].apply(lambda x: "Active" if x in active_user_emails else "Inactive")
        st.dataframe(users_df)

        #Classifying Report Status
        # Convert artifact IDs to a set for faster lookup
        active_artifact_ids = set(latest_access1["ArtifactId"])
        # Define a function to check if either ID or dataset ID is in the artifact list
        dataset_to_report = reports_df[["datasetId", "id"]].dropna().drop_duplicates()
        dataset_to_report_dict = dict(zip(dataset_to_report["datasetId"], dataset_to_report["id"]))

        def get_status(row):
            return "Active" if row["id"] in active_artifact_ids or row["datasetId"] in active_artifact_ids else "Inactive"
        #def get_da_status(row):
           # return "Active" if row["id"] in active_artifact_ids else "Inactive"
        def get_da_status(row):
            dataset_id = row["id"]
            related_report_id = dataset_to_report_dict.get(dataset_id)
            
            return "Active" if (
                dataset_id in active_artifact_ids or 
                (related_report_id and related_report_id in active_artifact_ids)
            ) else "Inactive"

        # Apply the function row-wise
        reports_df["activityStatus2"] = reports_df.apply(get_status, axis=1)
        datasets_df["activityStatus2"] = datasets_df.apply(get_da_status, axis=1)
        # Prepare a lookup dictionary: ArtifactId → Latest Activity
        artifact_activity_map = dict(zip(latest_access1["ArtifactId"], latest_access1["Latest Activity"]))

        # ------------------ Reports DF ------------------

        def get_report_activity(row):
            report_time = artifact_activity_map.get(row["id"])
            if report_time:
                return report_time
            elif pd.notna(row.get("datasetId")):
                return artifact_activity_map.get(row["datasetId"])
            return None


        reports_df["Latest Artifact Activity"] = reports_df.apply(get_report_activity, axis=1)

        # ------------------ Datasets DF ------------------

        #def get_dataset_activity(row):
            # Just check dataset ID
           # return artifact_activity_map.get(row["id"])
        # Step 1: Build a lookup table for datasetId → reportId
       
        # Step 2: Define fallback activity lookup function
        def get_dataset_activity(row):
            dataset_id = row["id"]
            # First, try using the dataset ID
            activity = artifact_activity_map.get(dataset_id)
            if activity:
                return activity
            # Fallback: lookup report that uses this dataset
            report_id = dataset_to_report_dict.get(dataset_id)
            if report_id:
                return artifact_activity_map.get(report_id)
            return None  # Neither found


        datasets_df["Latest Artifact Activity"] = datasets_df.apply(get_dataset_activity, axis=1)


        # Display the updated DataFrame
        st.dataframe(reports_df)
        st.dataframe(datasets_df)                

    else:
        st.warning("❌ Could not fetch all data. Please check your token and workspace ID.")
else:
    st.info("🔑 Enter your access token and workspace ID in the sidebar to begin.")
