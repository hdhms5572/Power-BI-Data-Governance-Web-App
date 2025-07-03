import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes
from utils import apply_sidebar_style, show_workspace_header

# Apply styles and headers
apply_sidebar_style()
show_workspace_header()

st.title("🔍 Activity Log Insights")

# ------------------ Credential Check ------------------
if not (st.session_state.get("access_token") and st.session_state.get("workspace_id") and st.session_state.get("user_email")):
    st.warning("❌ Missing credentials. Please authenticate on the main page.")
    st.stop()

# ------------------ Session Variables ------------------
token = st.session_state.access_token
workspace = st.session_state.workspace_id
email = st.session_state.user_email

# ------------------ Load Workspace Data ------------------
reports_df, datasets_df, users_df = get_filtered_dataframes(token, workspace, email)

# ------------------ Upload CSV ------------------
activity_data = st.file_uploader("📤 Upload activity CSV file")
if activity_data:
    activity_df = pd.read_csv(activity_data)
    domain = email.split("@")[1]
    filtered_df = activity_df[activity_df.get("User email", "").str.endswith(domain, na=False)]

    filtered_df["Activity time"] = pd.to_datetime(filtered_df["Activity time"], errors="coerce")
    filtered_df = filtered_df.sort_values("Activity time")

    latest_access_df = filtered_df.drop_duplicates(subset="Artifact Name", keep="last")
    latest_access_df.rename(columns={"Activity time": "Latest Activity"}, inplace=True)
    # Reset index and add serial number
    latest_access_df = latest_access_df.reset_index(drop=True)
    


    # Artifact classification
    report_ids = set(reports_df["id"])
    dataset_ids = set(datasets_df["id"])
    def classify_type(artifact_id):
        if artifact_id in report_ids:
            return "Report"
        elif artifact_id in dataset_ids:
            return "Dataset"
        return "Unknown"
    latest_access_df["ArtifactType"] = latest_access_df["ArtifactId"].apply(classify_type)

    # Active users and artifacts
    active_users = filtered_df["User email"].dropna().unique()
    users_df["activityStatus"] = users_df["emailAddress"].apply(lambda x: "Active" if x in active_users else "Inactive")

    active_artifacts = set(latest_access_df["ArtifactId"])
    dataset_to_report = dict(zip(reports_df["datasetId"], reports_df["id"]))

    reports_df["activityStatus2"] = reports_df.apply(
        lambda row: "Active" if row["id"] in active_artifacts or row["datasetId"] in active_artifacts else "Inactive", axis=1)
    datasets_df["activityStatus2"] = datasets_df.apply(
        lambda row: "Active" if row["id"] in active_artifacts or dataset_to_report.get(row["id"]) in active_artifacts else "Inactive", axis=1)

    artifact_activity_map = dict(zip(latest_access_df["ArtifactId"], latest_access_df["Latest Activity"]))
    reports_df["Latest Artifact Activity"] = reports_df.apply(
        lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(row["datasetId"]), axis=1)
    datasets_df["Latest Artifact Activity"] = datasets_df.apply(
        lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(dataset_to_report.get(row["id"])), axis=1)

    # ------------------ Expander Sections ------------------
    with st.expander("📁 Raw Activity Data"):
        st.dataframe(activity_df, use_container_width=True)

    with st.expander("📌 Most Recently Accessed Artifacts"):
        st.dataframe(latest_access_df, use_container_width=True)

    with st.expander("👥 Users Activity Status"):
        st.dataframe(users_df, use_container_width=True)
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.countplot(data=users_df, x="activityStatus", palette={"Active": "green", "Inactive": "red"}, ax=ax)
        ax.set_title("User Activity")
        st.pyplot(fig)

    with st.expander("📊 Reports and Datasets Latest Activity"):
        st.markdown("**Reports**")
        st.dataframe(reports_df, use_container_width=True)
        st.markdown("**Datasets**")
        st.dataframe(datasets_df, use_container_width=True)

    with st.expander("📈 Usage Trends"):
        col1, col2 = st.columns(2)
        with col1:
            top_reports = filtered_df["Artifact Name"].value_counts().head(10).reset_index()
            top_reports.columns = ["Report Name", "Access Count"]
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.barplot(data=top_reports, x="Access Count", y="Report Name", palette="crest", ax=ax)
            ax.set_title("Top Accessed Reports")
            st.pyplot(fig)

        with col2:
            filtered_df["YearMonth"] = filtered_df["Activity time"].dt.to_period("M").astype(str)
            monthly_usage = filtered_df.groupby("YearMonth").size().reset_index(name="Access Count")
            monthly_usage["YearMonth"] = pd.to_datetime(monthly_usage["YearMonth"])
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
            ax.set_title("Monthly Usage Trend")
            ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
            st.pyplot(fig)

    with st.expander("📅 Weekly and Hourly Access Patterns"):
        col3, col4 = st.columns(2)
        with col3:
            filtered_df["Weekday"] = filtered_df["Activity time"].dt.day_name()
            weekday_counts = filtered_df["Weekday"].value_counts().reindex([
                "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
            ])
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.barplot(x=weekday_counts.index, y=weekday_counts.values, palette="flare", ax=ax)
            ax.set_title("Weekday Activity")
            st.pyplot(fig)

        with col4:
            filtered_df["Hour"] = filtered_df["Activity time"].dt.hour
            hour_counts = filtered_df["Hour"].value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.lineplot(x=hour_counts.index, y=hour_counts.values, marker='o', color="teal", ax=ax)
            ax.set_title("Hourly Access Trend")
            ax.set_xlabel("Hour")
            ax.set_ylabel("Count")
            st.pyplot(fig)

    with st.expander("⚙️ Activity Type Distribution"):
        if "Activity" in filtered_df.columns:
            activity_counts = filtered_df["Activity"].value_counts().reset_index()
            activity_counts.columns = ["Activity Type", "Count"]
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.barplot(data=activity_counts, x="Count", y="Activity Type", palette="Set2", ax=ax)
            ax.set_title("Activity Types")
            st.pyplot(fig)

    with st.expander("📊 Artifact Access Heatmap"):
        heatmap_data = filtered_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax)
        ax.set_title("User vs Artifact Access")
        st.pyplot(fig)

    with st.expander("📦 Artifact Type Share"):
        if "Type" in filtered_df.columns:
            type_counts = filtered_df["Type"].value_counts()
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.pie(type_counts.values, labels=type_counts.index, autopct="%1.1f%%", startangle=135,
                   colors=sns.color_palette("Pastel1"))
            ax.set_title("Artifact Type Distribution")
            ax.axis("equal")
            st.pyplot(fig)
