import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

apply_sidebar_style()
show_workspace()

st.markdown("<h1 style='text-align: center;'>🔍 Activity Log Insights</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

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
    activity_df2=activity_df


    activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
    activity_df = activity_df.sort_values("Activity time")
    latest_access1 = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
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

    active_user_emails = activity_df["User email"].dropna().unique()
    users_df["activityStatus"] = users_df["emailAddress"].apply(lambda x: "Active" if x in active_user_emails else "Inactive")

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


    with st.expander("📊 User Insights"):
        col1, col2 = st.columns([2,1])
        with col1:
            st.subheader("Artifact Access Heatmap")
            heatmap_data = activity_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
            fig, ax = plt.subplots(figsize=(12,3))
            fig.patch.set_alpha(0.01)
            ax.patch.set_alpha(0.01)   
            ax.title.set_color('black')
            ax.xaxis.label.set_color('black')
            ax.yaxis.label.set_color('black')
            ax.tick_params(colors='black')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color('black')
            sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax, cbar=False)
            ax.set_title("Access Heatmap")
            st.pyplot(fig)
        with col2:
            st.subheader("User Activity Status")
            fig, ax = plt.subplots(figsize=(4, 3))
            fig.patch.set_alpha(0.01)
            ax.patch.set_alpha(0.01 )   
            ax.title.set_color('black')
            ax.xaxis.label.set_color('black')
            ax.yaxis.label.set_color('black')
            ax.tick_params(colors='black')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color('black')  
            sns.countplot(data=users_df, x="activityStatus", palette={"Active": "green", "Inactive": "red"}, ax=ax)
            ax.set_title("User Activity")
            st.pyplot(fig)

    with st.expander("📈 Usage Trends"):
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Top 10 Accessed Reports")
            top_reports = activity_df["Artifact Name"].value_counts().head(10).reset_index()
            top_reports.columns = ["Report Name", "Access Count"]
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_alpha(0.01)
            ax.patch.set_alpha(0.01)   
            ax.title.set_color('black')
            ax.xaxis.label.set_color('black')
            ax.yaxis.label.set_color('black')
            ax.tick_params(colors='black')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color('black')
            sns.barplot(data=top_reports, x="Access Count", y="Report Name", palette="crest", ax=ax)
            ax.set_title("Top Reports")
            st.pyplot(fig)
        with col4:
            st.subheader("Monthly Usage Trend")
            activity_df["YearMonth"] = activity_df["Activity time"].dt.to_period("M").astype(str)
            monthly_usage = activity_df.groupby("YearMonth").size().reset_index(name="Access Count")
            monthly_usage["YearMonth"] = pd.to_datetime(monthly_usage["YearMonth"])
            monthly_usage = monthly_usage.sort_values("YearMonth")
            fig, ax = plt.subplots(figsize=(6, 2))
            fig.patch.set_alpha(0.01)
            ax.patch.set_alpha(0.01)   
            ax.title.set_color('black')
            ax.xaxis.label.set_color('black')
            ax.yaxis.label.set_color('black')
            ax.tick_params(colors='black')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color('black')
            sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
            ax.set_title("Monthly Usage")
            ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
            st.pyplot(fig)

    with st.expander("📅 Weekly and Hourly Access Patterns"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Weekday Activity")
            activity_df["Weekday"] = activity_df["Activity time"].dt.day_name()
            weekday_counts = activity_df["Weekday"].value_counts().reindex([
                "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
            ])
            fig, ax = plt.subplots(figsize=(6, 3))
            fig.patch.set_alpha(0.01)
            ax.patch.set_alpha(0.01)
            ax.set_facecolor("none")
            sns.barplot(x=weekday_counts.index, y=weekday_counts.values, palette="flare", ax=ax)
            ax.set_title("Weekday Activity", color="black")
            ax.set_xlabel("Day", color="black")
            ax.set_ylabel("Activity Count", color="black")
            ax.tick_params(colors="black")
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color("black")
            st.pyplot(fig)

        with col2:
            st.subheader("Hourly Access Trend")
            activity_df["Hour"] = activity_df["Activity time"].dt.hour
            hour_counts = activity_df["Hour"].value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(6, 3))
            fig.patch.set_alpha(0.01)
            ax.patch.set_alpha(0.01)
            ax.set_facecolor("none")
            sns.lineplot(x=hour_counts.index, y=hour_counts.values, marker='o', color="teal", ax=ax)
            ax.set_title("Hourly Access Trend", color="black")
            ax.set_xlabel("Hour", color="black")
            ax.set_ylabel("Access Count", color="black")
            ax.tick_params(colors="black")
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color("black")
            st.pyplot(fig)


    st.markdown("""<hr style="margin-top:3rem; margin-bottom:2rem;">""", unsafe_allow_html=True)

    activity_options = {
        "-- Select an insight --": None,
        "📁 Activity Log Insights": "activity",
        "📌 Recently Accessed Artifacts": "recent",
        "🧍‍♂️ Users Activity Status": "users",
        "📈 Reports Latest Activity": "reports",
        "🗃️ Datasets Latest Activity": "datasets"
    }

    selected_key = st.selectbox(
        "🔍 Select insight to explore:",
        options = list(activity_options.keys())
    )


    selected_value = activity_options[selected_key]
    if selected_value == "activity":
        st.subheader("📁 Activity Log Insights")
        st.dataframe(activity_df2)

    elif selected_value == "recent":
        st.subheader("📌 Most Recently Accessed Artifacts")
        latest_access1 = latest_access1.reset_index(drop=True)
        st.dataframe(latest_access1)

    elif selected_value == "users":
        st.subheader("📌 Users Activity Status")
        st.dataframe(users_df)

    elif selected_value == "reports":
        st.subheader("📌 Reports Latest Activity")
        st.dataframe(reports_df)

    elif selected_value == "datasets":
        st.subheader("📌 Datasets Latest Activity")
        st.dataframe(datasets_df)
        
    st.markdown("""<hr style="margin-top:1rem; margin-bottom:1rem;">""", unsafe_allow_html=True)
