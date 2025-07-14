'''import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

apply_sidebar_style()
show_workspace()

st.markdown("<h1 style='text-align: center;'>🔍 Activity Log Insights</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Validate session state
if not (st.session_state.get("access_token") and st.session_state.get("workspace_ids") and st.session_state.get("user_email")):
    st.warning("❌ Missing credentials or workspace selection.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Aggregate reports/datasets/users across selected workspaces
reports_df_list, datasets_df_list, users_df_list = [], [], []
for ws_id in workspace_ids:
    reports, datasets, users = get_filtered_dataframes(token, ws_id, email)
    workspace_name = workspace_map.get(ws_id, "Unknown")
    for df in [reports, datasets, users]:
        df["workspace_id"] = ws_id
        df["workspace_name"] = workspace_name
    reports_df_list.append(reports)
    datasets_df_list.append(datasets)
    users_df_list.append(users)

reports_df = pd.concat(reports_df_list, ignore_index=True)
datasets_df = pd.concat(datasets_df_list, ignore_index=True)
users_df = pd.concat(users_df_list, ignore_index=True)

# Load activity log data
activity_data = "sample_analysis/data.csv"  # or use: st.file_uploader(...)
if activity_data:
    activity_df = pd.read_csv(activity_data)
    activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
    activity_df = activity_df.sort_values("Activity time")

    latest_access = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
    latest_access.rename(columns={"Activity time": "Latest Activity"}, inplace=True)

    # Map and mark activity status
    report_ids = set(reports_df["id"])
    dataset_ids = set(datasets_df["id"])
    dataset_to_report = dict(zip(reports_df["datasetId"], reports_df["id"]))
    active_users = activity_df["User email"].dropna().unique()
    users_df["activityStatus"] = users_df["emailAddress"].apply(lambda x: "Active" if x in active_users else "Inactive")

    active_artifacts = set(latest_access["ArtifactId"])
    artifact_activity_map = dict(zip(latest_access["ArtifactId"], latest_access["Latest Activity"]))

    reports_df["Activity Status"] = reports_df.apply(
        lambda row: "Active" if row["id"] in active_artifacts or row["datasetId"] in active_artifacts else "Inactive", axis=1)
    reports_df["Latest Artifact Activity"] = reports_df.apply(
        lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(row["datasetId"]), axis=1)

    datasets_df["Activity Status"] = datasets_df.apply(
        lambda row: "Active" if row["id"] in active_artifacts or dataset_to_report.get(row["id"]) in active_artifacts else "Inactive", axis=1)
    datasets_df["Latest Artifact Activity"] = datasets_df.apply(
        lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(dataset_to_report.get(row["id"])), axis=1)

    # Theme base adjustment
    fig_alpha = 1.0 if st.get_option("theme.base") == "dark" else 0.01

    # User Insights
    with st.expander("📊 User Insights"):
        col1, col2 = st.columns([4, 2])
        with col1:
            st.subheader("Artifact Access Heatmap")
            heatmap_data = activity_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
            fig, ax = plt.subplots(figsize=(5, 3))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax, cbar=False)
            ax.set_title("Access Heatmap", color="gray")
            ax.tick_params(colors='gray')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color('gray')
            st.pyplot(fig)
        with col2:
            st.subheader("User Activity Status")
            fig, ax = plt.subplots(figsize=(3, 5))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            sns.countplot(data=users_df, x="activityStatus", palette={"Active": "green", "Inactive": "red"}, ax=ax)
            ax.set_title("User Activity", color="gray")
            ax.tick_params(colors='gray')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color("gray")
            st.pyplot(fig)

    # Usage Trends
    with st.expander("📈 Usage Trends"):
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Top 10 Accessed Artifacts")
            top_reports = activity_df["Artifact Name"].value_counts().head(10).reset_index()
            top_reports.columns = ["Artifact Name", "Access Count"]
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            sns.barplot(data=top_reports, x="Access Count", y="Artifact Name", palette="crest", ax=ax)
            ax.set_title("Top Artifacts", color="gray")
            ax.tick_params(colors='gray')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color('gray')
            st.pyplot(fig)
        with col4:
            st.subheader("Usage Trends By Opcos")
            unique_users = activity_df.drop_duplicates(subset='User email')
            unique_users["domain"] = unique_users["User email"].str.split('@').str[-1]
            domain_counts = unique_users["domain"].value_counts()
            fig, ax = plt.subplots(figsize=(7, 2))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            ax.bar(domain_counts.index, domain_counts.values, color='skyblue')
            ax.set_title("Users per Opcos", color="gray")
            ax.set_xlabel("Email Domain", color="gray")
            ax.set_ylabel("Number of Users", color="gray")
            ax.tick_params(axis='x', rotation=45, colors='gray')
            st.pyplot(fig)

    # Weekly & Monthly Access Patterns
    with st.expander("📅 Weekly and Monthly Access Patterns"):
        col5, col6 = st.columns(2)
        with col5:
            st.subheader("📆 Weekday Activity")
            activity_df["Weekday"] = activity_df["Activity time"].dt.day_name()
            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekday_counts = activity_df["Weekday"].value_counts().reindex(weekday_order)
            fig, ax = plt.subplots(figsize=(6, 3))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            ax.plot(weekday_counts.index, weekday_counts.values, marker='o', linestyle='-', color='orange')
            ax.set_title("Weekday Activity", color="gray")
            ax.tick_params(colors='gray')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color("gray")
            st.pyplot(fig)
        with col6:
            st.subheader("📆 Monthly Usage Trend")
            activity_df["YearMonth"] = activity_df["Activity time"].dt.to_period("M").astype(str)
            monthly_usage = activity_df.groupby("YearMonth").size().reset_index(name="Access Count")
            monthly_usage["YearMonth"] = pd.to_datetime(monthly_usage["YearMonth"])
            monthly_usage = monthly_usage.sort_values("YearMonth")
            fig, ax = plt.subplots(figsize=(6, 2))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
            ax.set_title("Monthly Usage", color="gray")
            ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
            ax.tick_params(colors='gray')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color("gray")
            st.pyplot(fig)

    st.markdown("""<hr style="margin-top:3rem; margin-bottom:2rem;">""", unsafe_allow_html=True)


    activity_options = {
        "-- Select an insight --": None,
        "📁 Activity Log Insights": "activity",
        "📌 Recently Accessed Artifacts": "recent",
        "🧍‍♂️ Users Activity Status": "users",
        "📈 Reports Latest Activity": "reports",
        "🗃️ Datasets Latest Activity": "datasets",
        "📭 Unused Artifacts": "artifacts"
    }

    selected_key = st.selectbox(
        "🔍 Select insight to explore:",
        options = list(activity_options.keys())
    )


    selected_value = activity_options[selected_key]
    if selected_value == "activity":
        st.subheader("📁 Activity Log Insights")
        st.dataframe(activity_df)

    elif selected_value == "recent":
        st.subheader("📌 Most Recently Accessed Artifacts")
        latest_access1 = latest_access.reset_index(drop=True)
        st.dataframe(latest_access1)

    elif selected_value == "users":
        st.subheader("📌 Users Activity Status")
        st.dataframe(users_df)

    elif selected_value == "reports":
        st.subheader("📌 Reports Latest Activity")
        st.dataframe(reports_df[["id", "name","datasetId","datasetStatus","outdated","Reportstatus Based on Dataset","Activity Status","Latest Artifact Activity"]])

    elif selected_value == "datasets":
        st.subheader("📌 Datasets Latest Activity")
        st.dataframe(datasets_df)

    elif selected_value == "artifacts":
        report_names = reports_df["name"]
        dataset_names = datasets_df["name"]
        all_artifact_names = pd.concat([report_names, dataset_names], ignore_index=True).dropna().unique()
        used_artifact_names = activity_df["Artifact Name"].dropna().unique()
        artifact_status_df = pd.DataFrame(all_artifact_names, columns=["Artifact Name"])
        artifact_status_df["Usage Status"] = artifact_status_df["Artifact Name"].apply(
            lambda x: "Used" if x in used_artifact_names else "Unused"
        )
        unused_artifacts_df = artifact_status_df[artifact_status_df["Usage Status"] == "Unused"]
        st.subheader("📭 Unused Artifacts")
        st.dataframe(unused_artifacts_df, use_container_width=True)
        
    st.markdown("""<hr style="margin-top:1rem; margin-bottom:1rem;">""", unsafe_allow_html=True)'''


'''import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

apply_sidebar_style()
show_workspace()

st.markdown("<h1 style='text-align: center;'>🔍 Activity Log Insights</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Validate session state
if not (st.session_state.get("access_token") and st.session_state.get("workspace_ids") and st.session_state.get("user_email")):
    st.warning("❌ Missing credentials or workspace selection.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Aggregate reports/datasets/users across selected workspaces
reports_df_list, datasets_df_list, users_df_list = [], [], []
for ws_id in workspace_ids:
    reports, datasets, users = get_filtered_dataframes(token, ws_id, email)
    workspace_name = workspace_map.get(ws_id, "Unknown")
    for df in [reports, datasets, users]:
        df["workspace_id"] = ws_id
        df["workspace_name"] = workspace_name
    reports_df_list.append(reports)
    datasets_df_list.append(datasets)
    users_df_list.append(users)

reports_df = pd.concat(reports_df_list, ignore_index=True)
datasets_df = pd.concat(datasets_df_list, ignore_index=True)
users_df = pd.concat(users_df_list, ignore_index=True)

# Load activity log data
activity_data = "sample_analysis/data.csv"  # or use: st.file_uploader(...)
if activity_data:
    activity_df = pd.read_csv(activity_data)
    activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
    activity_df = activity_df.sort_values("Activity time")

    latest_access = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
    latest_access.rename(columns={"Activity time": "Latest Activity"}, inplace=True)

    # Map and mark activity status
    report_ids = set(reports_df["id"])
    dataset_ids = set(datasets_df["id"])
    dataset_to_report = dict(zip(reports_df["datasetId"], reports_df["id"]))
    active_users = activity_df["User email"].dropna().unique()
    users_df["activityStatus"] = users_df["emailAddress"].apply(lambda x: "Active" if x in active_users else "Inactive")

    active_artifacts = set(latest_access["ArtifactId"])
    artifact_activity_map = dict(zip(latest_access["ArtifactId"], latest_access["Latest Activity"]))

    reports_df["Activity Status"] = reports_df.apply(
        lambda row: "Active" if row["id"] in active_artifacts or row["datasetId"] in active_artifacts else "Inactive", axis=1)
    reports_df["Latest Artifact Activity"] = reports_df.apply(
        lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(row["datasetId"]), axis=1)

    datasets_df["Activity Status"] = datasets_df.apply(
        lambda row: "Active" if row["id"] in active_artifacts or dataset_to_report.get(row["id"]) in active_artifacts else "Inactive", axis=1)
    datasets_df["Latest Artifact Activity"] = datasets_df.apply(
        lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(dataset_to_report.get(row["id"])), axis=1)

    # Theme base adjustment
    fig_alpha = 1.0 if st.get_option("theme.base") == "dark" else 0.01

    # User Insights
    with st.expander("📊 User Insights"):
        col1, col2 = st.columns([4, 2])
        with col1:
            st.subheader("Artifact Access Heatmap")
            heatmap_data = activity_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
            fig, ax = plt.subplots(figsize=(5, 3))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax, cbar=False)
            ax.set_title("Access Heatmap", color="gray")
            ax.tick_params(colors='gray')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color('gray')
            st.pyplot(fig)
        with col2:
            st.subheader("User Activity Status")
            fig, ax = plt.subplots(figsize=(3, 5))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            sns.countplot(data=users_df, x="activityStatus", palette={"Active": "green", "Inactive": "red"}, ax=ax)
            ax.set_title("User Activity", color="gray")
            ax.tick_params(colors='gray')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color("gray")
            st.pyplot(fig)

    # Usage Trends
    with st.expander("📈 Usage Trends"):
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Top 10 Accessed Artifacts")
            top_reports = activity_df["Artifact Name"].value_counts().head(10).reset_index()
            top_reports.columns = ["Artifact Name", "Access Count"]
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            sns.barplot(data=top_reports, x="Access Count", y="Artifact Name", palette="crest", ax=ax)
            ax.set_title("Top Artifacts", color="gray")
            ax.tick_params(colors='gray')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color('gray')
            st.pyplot(fig)
        with col4:
            st.subheader("Usage Trends By Opcos")
            unique_users = activity_df.drop_duplicates(subset='User email')
            unique_users["domain"] = unique_users["User email"].str.split('@').str[-1]
            domain_counts = unique_users["domain"].value_counts()
            fig, ax = plt.subplots(figsize=(7, 2))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            ax.bar(domain_counts.index, domain_counts.values, color='skyblue')
            ax.set_title("Users per Opcos", color="gray")
            ax.set_xlabel("Email Domain", color="gray")
            ax.set_ylabel("Number of Users", color="gray")
            ax.tick_params(axis='x', rotation=45, colors='gray')
            st.pyplot(fig)

    # Weekly & Monthly Access Patterns
    with st.expander("📅 Weekly and Monthly Access Patterns"):
        col5, col6 = st.columns(2)
        with col5:
            st.subheader("📆 Weekday Activity")
            activity_df["Weekday"] = activity_df["Activity time"].dt.day_name()
            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekday_counts = activity_df["Weekday"].value_counts().reindex(weekday_order)
            fig, ax = plt.subplots(figsize=(6, 3))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            ax.plot(weekday_counts.index, weekday_counts.values, marker='o', linestyle='-', color='orange')
            ax.set_title("Weekday Activity", color="gray")
            ax.tick_params(colors='gray')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color("gray")
            st.pyplot(fig)
        with col6:
            st.subheader("📆 Monthly Usage Trend")
            activity_df["YearMonth"] = activity_df["Activity time"].dt.to_period("M").astype(str)
            monthly_usage = activity_df.groupby("YearMonth").size().reset_index(name="Access Count")
            monthly_usage["YearMonth"] = pd.to_datetime(monthly_usage["YearMonth"])
            monthly_usage = monthly_usage.sort_values("YearMonth")
            fig, ax = plt.subplots(figsize=(6, 2))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)
            sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
            ax.set_title("Monthly Usage", color="gray")
            ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
            ax.tick_params(colors='gray')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color("gray")
            st.pyplot(fig)

    st.markdown("""<hr style="margin-top:3rem; margin-bottom:2rem;">""", unsafe_allow_html=True)


    activity_options = {
        "-- Select an insight --": None,
        "📁 Activity Log Insights": "activity",
        "📌 Recently Accessed Artifacts": "recent",
        "🧍‍♂️ Users Activity Status": "users",
        "📈 Reports Latest Activity": "reports",
        "🗃️ Datasets Latest Activity": "datasets",
        "📭 Unused Artifacts": "artifacts"
    }

    selected_key = st.selectbox(
        "🔍 Select insight to explore:",
        options = list(activity_options.keys())
    )


    selected_value = activity_options[selected_key]
    if selected_value == "activity":
        st.subheader("📁 Activity Log Insights")
        st.dataframe(activity_df)

    elif selected_value == "recent":
        st.subheader("📌 Most Recently Accessed Artifacts")
        latest_access1 = latest_access.reset_index(drop=True)
        st.dataframe(latest_access1)

    elif selected_value == "users":
        st.subheader("📌 Users Activity Status")
        st.dataframe(users_df)

    elif selected_value == "reports":
        st.subheader("📌 Reports Latest Activity")
        st.dataframe(reports_df[["id", "name","datasetId","datasetStatus","outdated","Reportstatus Based on Dataset","Activity Status","Latest Artifact Activity"]])

    elif selected_value == "datasets":
        st.subheader("📌 Datasets Latest Activity")
        st.dataframe(datasets_df)

    elif selected_value == "artifacts":
        report_names = reports_df["name"]
        dataset_names = datasets_df["name"]
        all_artifact_names = pd.concat([report_names, dataset_names], ignore_index=True).dropna().unique()
        used_artifact_names = activity_df["Artifact Name"].dropna().unique()
        artifact_status_df = pd.DataFrame(all_artifact_names, columns=["Artifact Name"])
        artifact_status_df["Usage Status"] = artifact_status_df["Artifact Name"].apply(
            lambda x: "Used" if x in used_artifact_names else "Unused"
        )
        unused_artifacts_df = artifact_status_df[artifact_status_df["Usage Status"] == "Unused"]
        st.subheader("📭 Unused Artifacts")
        st.dataframe(unused_artifacts_df, use_container_width=True)
        
    st.markdown("""<hr style="margin-top:1rem; margin-bottom:1rem;">""", unsafe_allow_html=True)'''


import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

apply_sidebar_style()
show_workspace()

st.markdown("<h1 style='text-align: center;'>🔍 Activity Log Insights</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Validate session state
if not (st.session_state.get("access_token") and st.session_state.get("workspace_ids") and st.session_state.get("user_email")):
    st.warning("❌ Missing credentials or workspace selection.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Aggregate reports/datasets/users across selected workspaces
reports_df_list, datasets_df_list, users_df_list = [], [], []
for ws_id in workspace_ids:
    reports, datasets, users = get_filtered_dataframes(token, ws_id, email)
    workspace_name = workspace_map.get(ws_id, "Unknown")
    for df in [reports, datasets, users]:
        df["workspace_id"] = ws_id
        df["workspace_name"] = workspace_name
    reports_df_list.append(reports)
    datasets_df_list.append(datasets)
    users_df_list.append(users)

reports_df = pd.concat(reports_df_list, ignore_index=True)
datasets_df = pd.concat(datasets_df_list, ignore_index=True)
users_df = pd.concat(users_df_list, ignore_index=True)

activity_data = r"sample_analysis\data.csv"  
activity_df = pd.read_csv(activity_data)
activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
activity_df = activity_df.sort_values("Activity time")
latest_access = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
latest_access.rename(columns={"Activity time": "Latest Activity"}, inplace=True)
report_ids = set(reports_df["id"])
dataset_ids = set(datasets_df["id"])
dataset_to_report = dict(zip(reports_df["datasetId"], reports_df["id"]))
active_users = activity_df["User email"].dropna().unique()    
cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=3)
recent_user_activity = activity_df[activity_df["Activity time"] >= cutoff_date]
active_users = recent_user_activity["User email"].dropna().unique()
users_df["activityStatus"] = users_df["emailAddress"].apply(
    lambda x: "Active" if x in active_users else "Inactive"
)

# Map latest activity time by user email
user_latest_activity_map = activity_df.sort_values("Activity time").drop_duplicates(subset="User email", keep="last")
user_latest_activity_map = user_latest_activity_map.set_index("User email")["Activity time"]

users_df["Latest Activity Time"] = users_df["emailAddress"].map(user_latest_activity_map)

active_artifacts = set(latest_access["ArtifactId"])
artifact_activity_map = dict(zip(latest_access["ArtifactId"], latest_access["Latest Activity"]))

reports_df["Activity Status"] = reports_df.apply(
    lambda row: "Active" if row["id"] in active_artifacts or row["datasetId"] in active_artifacts else "Inactive", axis=1)
reports_df["Latest Artifact Activity"] = reports_df.apply(
    lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(row["datasetId"]), axis=1)

datasets_df["Activity Status"] = datasets_df.apply(
    lambda row: "Active" if row["id"] in active_artifacts or dataset_to_report.get(row["id"]) in active_artifacts else "Inactive", axis=1)
datasets_df["Latest Artifact Activity"] = datasets_df.apply(
    lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(dataset_to_report.get(row["id"])), axis=1)

fig_alpha = 1.0 if st.get_option("theme.base") == "dark" else 0.01
with st.expander("📊 User Insights"):
    col1, col2 = st.columns([4, 2])
    with col1:
        st.subheader("Artifact Access Heatmap")
        heatmap_data = activity_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(5, 3))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax, cbar=False)
        ax.set_title("Access Heatmap", color="gray")
        ax.tick_params(colors='gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color('gray')
        st.pyplot(fig)
    with col2:
        st.subheader("User Activity Status")
        fig, ax = plt.subplots(figsize=(3, 5))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        sns.countplot(data=users_df, x="activityStatus", palette={"Active": "green", "Inactive": "red"}, ax=ax)
        ax.set_title("User Activity", color="gray")
        ax.tick_params(colors='gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color("gray")
        st.pyplot(fig)

# Usage Trends
with st.expander("📈 Usage Trends"):
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top 10 Accessed Artifacts")
        top_reports = activity_df["Artifact Name"].value_counts().head(10).reset_index()
        top_reports.columns = ["Artifact Name", "Access Count"]
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        sns.barplot(data=top_reports, x="Access Count", y="Artifact Name", palette="crest", ax=ax)
        ax.set_title("Top Artifacts", color="gray")
        ax.tick_params(colors='gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color('gray')
        st.pyplot(fig)
    with col4:
        st.subheader("Usage Trends By Opcos")
        unique_users = activity_df.drop_duplicates(subset='User email')
        unique_users["domain"] = unique_users["User email"].str.split('@').str[-1]
        domain_counts = unique_users["domain"].value_counts()
        fig, ax = plt.subplots(figsize=(7, 2))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        ax.bar(domain_counts.index, domain_counts.values, color='skyblue')
        ax.set_title("Users per Opcos", color="gray")
        ax.set_xlabel("Email Domain", color="gray")
        ax.set_ylabel("Number of Users", color="gray")
        ax.tick_params(axis='x', rotation=45, colors='gray')
        st.pyplot(fig)

# Weekly & Monthly Access Patterns
with st.expander("📅 Weekly and Monthly Access Patterns"):
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("📆 Weekday Activity")
        activity_df["Weekday"] = activity_df["Activity time"].dt.day_name()
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_counts = activity_df["Weekday"].value_counts().reindex(weekday_order)
        fig, ax = plt.subplots(figsize=(6, 3))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        ax.plot(weekday_counts.index, weekday_counts.values, marker='o', linestyle='-', color='orange')
        ax.set_title("Weekday Activity", color="gray")
        ax.tick_params(colors='gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color("gray")
        st.pyplot(fig)
    with col6:
        st.subheader("📆 Monthly Usage Trend")
        activity_df["YearMonth"] = activity_df["Activity time"].dt.to_period("M").astype(str)
        monthly_usage = activity_df.groupby("YearMonth").size().reset_index(name="Access Count")
        monthly_usage["YearMonth"] = pd.to_datetime(monthly_usage["YearMonth"])
        monthly_usage = monthly_usage.sort_values("YearMonth")
        fig, ax = plt.subplots(figsize=(6, 2))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
        ax.set_title("Monthly Usage", color="gray")
        ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
        ax.tick_params(colors='gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color("gray")
        st.pyplot(fig)
            


st.markdown("""<hr style="margin-top:3rem; margin-bottom:2rem;">""", unsafe_allow_html=True)

activity_options = {
    "-- Select an insight --": None,
    "📁 Activity Log Insights": "activity",
    "📌 Recently Accessed Artifacts": "recent",
    "🧍‍♂️ Users Activity Status": "users",
    "📈 Reports Latest Activity": "reports",
    "🗃️ Datasets Latest Activity": "datasets",
    "📭 Unused Artifacts": "artifacts",
}

selected_key = st.selectbox(
    "🔍 Select insight to explore:",
    options = list(activity_options.keys())
)


selected_value = activity_options[selected_key]
if selected_value == "activity":
    st.subheader("📁 Activity Log Insights")
    activity_df.reset_index(drop=True, inplace=True)

    st.dataframe(activity_df[["Activity time","User email", "Activity", "ArtifactId", "Artifact Name"]])



elif selected_value == "recent":
    st.subheader("📌 Most Recently Accessed Artifacts")
    latest_access1 = latest_access.reset_index(drop=True)
    st.dataframe(latest_access1)

elif selected_value == "users":
    st.subheader("📌 Users Activity Status")
    st.dataframe(users_df[["emailAddress", "groupUserAccessRight", "displayName", "workspace_name","activityStatus","Latest Activity Time"]])

elif selected_value == "reports":
    st.subheader("📌 Reports Latest Activity")
    st.dataframe(reports_df[["id", "name","datasetId","datasetStatus","outdated","Reportstatus Based on Dataset","Activity Status","Latest Artifact Activity"]])

elif selected_value == "datasets":
    st.subheader("📌 Datasets Latest Activity")
    st.dataframe(datasets_df)

elif selected_value == "artifacts":
    report_names = reports_df["name"]
    dataset_names = datasets_df["name"]
    all_artifact_names = pd.concat([report_names, dataset_names], ignore_index=True).dropna().unique()
    used_artifact_names = activity_df["Artifact Name"].dropna().unique()
    artifact_status_df = pd.DataFrame(all_artifact_names, columns=["Artifact Name"])
    artifact_status_df["Usage Status"] = artifact_status_df["Artifact Name"].apply(
        lambda x: "Used" if x in used_artifact_names else "Unused"
    )
    unused_artifacts_df = artifact_status_df[artifact_status_df["Usage Status"] == "Unused"]
    st.subheader("📭 Unused Artifacts")
    st.dataframe(unused_artifacts_df, use_container_width=True)

st.markdown("""<hr style="margin-top:1rem; margin-bottom:1rem;">""", unsafe_allow_html=True)


st.subheader("🗂️ Artifact Action Breakdown")
with st.expander("Filter & Explore Actions", expanded=True):
    # Collect filter inputs
    search_term = st.text_input("🔍 Search by artifact name, user email, or activity type", key="search_term")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("📅 Start Date", value=None, key="start_date")
    with col2:
        end_date = st.date_input("📅 End Date", value=None, key="end_date")

    if st.button("🔍 Search"):
        st.session_state.run_filter = True

    if st.session_state.get("run_filter", False):
        filtered_df = activity_df.copy()
        
        if st.session_state.start_date:
            filtered_df = filtered_df[filtered_df["Activity time"] >= pd.to_datetime(st.session_state.start_date)]
        if st.session_state.end_date:
            filtered_df = filtered_df[filtered_df["Activity time"] <= pd.to_datetime(st.session_state.end_date)]

        # Apply keyword search
        if st.session_state.search_term:
            filtered_df = filtered_df[
                filtered_df["Artifact Name"].str.contains(st.session_state.search_term, case=False, na=False) |
                filtered_df["User email"].str.contains(st.session_state.search_term, case=False, na=False) |
                filtered_df["Activity"].str.contains(st.session_state.search_term, case=False, na=False)
            ]

        # Sort by latest activity time
        filtered_df = filtered_df.sort_values("Activity time", ascending=False).reset_index(drop=True)

        if "Activity" in filtered_df.columns:
            grouped_actions = filtered_df.groupby("Activity")
            for action, group in grouped_actions:
                with st.expander(f"🧩 {action} ({len(group)} activities)", expanded=False):
                    st.dataframe(group[["User email", "Artifact Name", "ArtifactId", "Activity time"]])
                    csv = group.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"{action}_activity_log.csv",
                        mime="text/csv"
                    )
        else:
            st.info("⚠️ 'Activity' column is missing from the dataset.")

        # Reset flag so it won't run again until explicitly triggered
        st.session_state.run_filter = False
     
