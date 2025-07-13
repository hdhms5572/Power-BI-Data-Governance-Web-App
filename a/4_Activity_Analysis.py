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

activity_data = r"C:\Users\10094790\Downloads\data (3).csv"  
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
                # Top Engagement Insights
    with st.expander("🏆 Top Engagement Insights"):
        col1, col2, col3 ,col4= st.columns(4)

        # Top Reports
        with col1:
            st.subheader("📊 Top 5 Reports")
            top_reports = activity_df[activity_df["ArtifactId"].isin(reports_df["id"])]
            report_usage = top_reports["ArtifactId"].value_counts().head(5).reset_index()
            report_usage.columns = ["Report ID", "Usage Count"]
            report_usage = report_usage.merge(reports_df[["id", "name"]], left_on="Report ID", right_on="id", how="left")
            fig1, ax1 = plt.subplots(figsize=(4, 3))
            fig1.patch.set_alpha(fig_alpha)
            ax1.patch.set_alpha(fig_alpha)
            sns.barplot(data=report_usage, x="Usage Count", y="name", palette="viridis", ax=ax1)
            ax1.set_title("Top Reports", color="gray")
            ax1.tick_params(colors='gray')
            for label in ax1.get_xticklabels() + ax1.get_yticklabels():
                label.set_color("gray")
            st.pyplot(fig1)

        # Top Datasets
        with col2:
            st.subheader("📦 Top 5 Datasets")
            top_datasets = activity_df[activity_df["ArtifactId"].isin(datasets_df["id"])]
            dataset_usage = top_datasets["ArtifactId"].value_counts().head(5).reset_index()
            dataset_usage.columns = ["Dataset ID", "Usage Count"]
            dataset_usage = dataset_usage.merge(datasets_df[["id", "name"]], left_on="Dataset ID", right_on="id", how="left")
            fig2, ax2 = plt.subplots(figsize=(4, 3))
            fig2.patch.set_alpha(fig_alpha)
            ax2.patch.set_alpha(fig_alpha)
            sns.barplot(data=dataset_usage, x="Usage Count", y="name", palette="crest", ax=ax2)
            ax2.set_title("Top Datasets", color="gray")
            ax2.tick_params(colors='gray')
            for label in ax2.get_xticklabels() + ax2.get_yticklabels():
                label.set_color("gray")
            st.pyplot(fig2)

        # Top Users
        with col3:
            st.subheader("👤 Top 5 Users")
            user_activity = activity_df["User email"].value_counts().head(5).reset_index()
            user_activity.columns = ["User Email", "Activity Count"]
            user_activity = user_activity.merge(users_df[["emailAddress", "displayName"]], left_on="User Email", right_on="emailAddress", how="left")
            fig3, ax3 = plt.subplots(figsize=(4, 3))
            fig3.patch.set_alpha(fig_alpha)
            ax3.patch.set_alpha(fig_alpha)
            sns.barplot(data=user_activity, x="Activity Count", y="displayName", palette="Blues_d", ax=ax3)
            ax3.set_title("Top Users", color="gray")
            ax3.tick_params(colors='gray')
            for label in ax3.get_xticklabels() + ax3.get_yticklabels():
                label.set_color("gray")
            st.pyplot(fig3)
        with col4:
            # 🧪 Step 1: Filter recent activity
            cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=3)
            recent_activity_df = activity_df[activity_df["Activity time"] >= cutoff_date]

            # 📊 Step 2: Count user activity
            recent_user_activity = recent_activity_df["User email"].value_counts().head(5).reset_index()
            recent_user_activity.columns = ["User Email", "Activity Count"]

            # 🧷 Step 3: Merge with user display names
            recent_user_activity = recent_user_activity.merge(
                users_df[["emailAddress", "displayName"]],
                left_on="User Email",
                right_on="emailAddress",
                how="left"
            )

            # 🎨 Step 4: Create barplot
            st.subheader("👤 Top 5 Active Users (Last 3 Months)")
            fig, ax = plt.subplots(figsize=(5, 3.5))
            fig.patch.set_alpha(fig_alpha)
            ax.patch.set_alpha(fig_alpha)

            sns.barplot(
                data=recent_user_activity,
                x="Activity Count",
                y="displayName",
                palette="Blues_d",
                ax=ax
            )

            ax.set_title("Top Users (3-Month Activity)", color="gray")
            ax.set_xlabel("Activity Count", color="gray")
            ax.set_ylabel("User", color="gray")
            ax.tick_params(colors="gray")

            # 🖌️ Gray out tick labels
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
        "🗂️ Artifact Action Breakdown": "action"
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
    elif selected_value == "action":
        st.subheader("🗂️ Artifact Action Breakdown")
        with st.expander("🔍 Grouped by Activity Type"):
            if "Activity" in activity_df.columns:
                grouped_actions = activity_df.groupby("Activity")
                for action, group in grouped_actions:
                    sorted_group = group.sort_values("Activity time", ascending=False).reset_index(drop=True)
                    with st.expander(f"🧩 {action} ({len(sorted_group)} activities)", expanded=False):
                        st.dataframe(sorted_group[["User email", "Artifact Name","ArtifactId", "Activity time"]])
            else:
                st.info("No 'Activity' column found in activity data.")

    st.markdown("""<hr style="margin-top:1rem; margin-bottom:1rem;">""", unsafe_allow_html=True)