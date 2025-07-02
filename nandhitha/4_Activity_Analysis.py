import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes
from utils import apply_sidebar_style
apply_sidebar_style()
from utils import show_workspace_header
show_workspace_header()

st.title("🔍 Activity Log Insights")

# Check for required session state values
if not (st.session_state.get("access_token") and st.session_state.get("workspace_id") and st.session_state.get("user_email")):
    st.warning("❌ Missing access token, workspace ID, or email. Please provide credentials in the main page.")
    st.stop()

# Retrieve from session state
token = st.session_state.access_token
workspace = st.session_state.workspace_id
email = st.session_state.user_email

reports_df, datasets_df, users_df = get_filtered_dataframes(token, workspace, email)

activity_data = st.file_uploader("Upload csv file...")
if activity_data:
    activity_df = pd.read_csv(activity_data)
    domain = email.split("@")[1]  # For RLS
    filtered_activity_df = activity_df[activity_df.get("User email", "").str.endswith(domain, na=False)]

    st.dataframe(filtered_activity_df)
    filtered_activity_df["Activity time"] = pd.to_datetime(filtered_activity_df["Activity time"], errors="coerce")
    filtered_activity_df = filtered_activity_df.sort_values("Activity time")
    latest_access1 = filtered_activity_df.drop_duplicates(subset="Artifact Name", keep="last")
    latest_access1.rename(columns={"Activity time": "Latest Activity"}, inplace=True)

    report_ids = set(reports_df["id"])
    dataset_ids = set(datasets_df["id"])

    def classify_artifact_type(artifact_id):
        if artifact_id in report_ids:
            return "Report"
        elif artifact_id in dataset_ids:
            return "Dataset"
        return "Unknown"

    latest_access1["ArtifactType"] = latest_access1["ArtifactId"].apply(classify_artifact_type)
    st.subheader("📌 Most Recently Accessed Artifacts")
    st.dataframe(latest_access1)

    active_user_emails = filtered_activity_df["User email"].dropna().unique()
    users_df["activityStatus"] = users_df["emailAddress"].apply(lambda x: "Active" if x in active_user_emails else "Inactive")
    st.subheader("📌 Users Activity Status")
    st.dataframe(users_df)

    active_artifact_ids = set(latest_access1["ArtifactId"])
    dataset_to_report_dict = dict(zip(reports_df["datasetId"], reports_df["id"]))

    reports_df["activityStatus2"] = reports_df.apply(
        lambda row: "Active" if row["id"] in active_artifact_ids or row["datasetId"] in active_artifact_ids else "Inactive", axis=1)

    datasets_df["activityStatus2"] = datasets_df.apply(
        lambda row: "Active" if row["id"] in active_artifact_ids or dataset_to_report_dict.get(row["id"]) in active_artifact_ids else "Inactive", axis=1)

    artifact_activity_map = dict(zip(latest_access1["ArtifactId"], latest_access1["Latest Activity"]))

    reports_df["Latest Artifact Activity"] = reports_df.apply(
        lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(row["datasetId"]), axis=1)

    datasets_df["Latest Artifact Activity"] = datasets_df.apply(
        lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(dataset_to_report_dict.get(row["id"])), axis=1)

    st.subheader("📌 Reports Latest Activity")
    st.dataframe(reports_df)

    st.subheader("📌 Datasets Latest Activity")
    st.dataframe(datasets_df)

    st.subheader("📊 User Insights")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**User Activity Status**")
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.countplot(data=users_df, x="activityStatus", palette={"Active": "green", "Inactive": "red"}, ax=ax)
        ax.set_title("User Activity")
        st.pyplot(fig)
    with col2:
        st.markdown("**Artifact Access Heatmap**")
        heatmap_data = filtered_activity_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax, cbar=False)
        ax.set_title("Access Heatmap")
        st.pyplot(fig)

    st.subheader("📈 Usage Trends")
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Top 10 Accessed Reports**")
        top_reports = filtered_activity_df["Artifact Name"].value_counts().head(10).reset_index()
        top_reports.columns = ["Report Name", "Access Count"]
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.barplot(data=top_reports, x="Access Count", y="Report Name", palette="crest", ax=ax)
        ax.set_title("Top Reports")
        st.pyplot(fig)
    with col4:
        st.markdown("**Monthly Usage Trend**")
        filtered_activity_df["YearMonth"] = filtered_activity_df["Activity time"].dt.to_period("M").astype(str)
        monthly_usage = filtered_activity_df.groupby("YearMonth").size().reset_index(name="Access Count")
        monthly_usage["YearMonth"] = pd.to_datetime(monthly_usage["YearMonth"])
        monthly_usage = monthly_usage.sort_values("YearMonth")
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
        ax.set_title("Monthly Usage")
        ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
        st.pyplot(fig)
