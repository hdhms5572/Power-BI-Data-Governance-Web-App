import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_cached_workspace_data, apply_sidebar_style, show_workspace
from utils import  render_profile_header, add_logout_button
from utils import handle_activity_upload,apply_activity_status

apply_sidebar_style()
def inject_external_style():
    with open("static/style.css") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
inject_external_style()

if not (st.session_state.get("access_token") and
        st.session_state.get("user_email")):
    st.warning("🔐 Authentication Required")
    st.stop()

add_logout_button()
render_profile_header()
show_workspace()

col1, col2, col3 = st.columns(3)
with col2:
    st.image("./images/dover_log.png")

st.markdown("<h1 style='text-align: center;'>🔍 Activity Log Insights</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; font-size: 1.05rem; background-color: #E7DBF3; padding: 14px 24px; border-left: 6px solid #673ab7; border-radius: 8px; margin-bottom: 25px;'>
This dashboard provides a centralized view of all user interactions with reports and datasets.
Explore usage trends, identify top artifacts and users, analyze activity patterns, and detect unused resources to improve data governance.
</div><hr>
""", unsafe_allow_html=True)


token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Aggregate reports/datasets/users across selected workspaces
reports_df_list, datasets_df_list, users_df_list = [], [], []
for ws_id in workspace_ids:
    reports, datasets, users = get_cached_workspace_data(token, ws_id, email)
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

activity_df = handle_activity_upload()
if activity_df is None or activity_df.empty:
    st.warning("⚠️ No activity data found. Please upload a valid activity CSV.")
    st.stop()


activity_df, reports_df, datasets_df, users_df, latest_access = apply_activity_status(
    activity_df, reports_df, datasets_df, users_df
)



with st.expander("📊 User Insights"):
        st.subheader("Artifact Access Heatmap")
        heatmap_data = activity_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(12, 6))  
        sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax, cbar=True)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        ax.set_title("Access Heatmap")
        st.pyplot(fig)

with st.expander("📈 Usage Trends"):
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top 10 Accessed Artifacts")
        top_reports = activity_df["Artifact Name"].value_counts().head(10).reset_index()
        top_reports.columns = ["Artifact Name", "Access Count"]
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(
            data=top_reports,
            x="Access Count",
            y="Artifact Name",
            palette=["#87CEEB"] * len(top_reports),  
        )
        ax.set_title("Top Artifacts")
        st.pyplot(fig)
    
  
    with col4:
        st.subheader("Usage Trends By Opcos")
        unique_users = activity_df.drop_duplicates(subset='User email')
        unique_users["domain"] = unique_users["User email"].str.split('@').str[-1]
        domain_counts = unique_users["domain"].value_counts()
        fig, ax = plt.subplots(figsize=(7, 2))
        ax.bar(domain_counts.index, domain_counts.values, color="#87CEEB")  # Sky blue bars
        ax.set_title("Users per Opcos")
        ax.set_xlabel("Email Domain")
        ax.set_ylabel("Number of Users")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

with st.expander("📅 Weekly and Monthly Access Patterns"):
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("📆 Weekday Activity")
        activity_df["Weekday"] = activity_df["Activity time"].dt.day_name()
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_counts = activity_df["Weekday"].value_counts().reindex(weekday_order)
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(weekday_counts.index, weekday_counts.values, marker='o', linestyle='-', color='orange')
        ax.set_title("Weekday Activity")
        st.pyplot(fig)
    with col6:
        st.subheader("📆 Monthly Usage Trend")
        activity_df["YearMonth"] = activity_df["Activity time"].dt.to_period("M").astype(str)
        monthly_usage = activity_df.groupby("YearMonth").size().reset_index(name="Access Count")
        monthly_usage["YearMonth"] = pd.to_datetime(monthly_usage["YearMonth"])
        monthly_usage = monthly_usage.sort_values("YearMonth")
        fig, ax = plt.subplots(figsize=(6, 2))
        sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
        ax.set_title("Monthly Usage")
        ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
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
    st.info("View all raw activity logs including who accessed what and when.")
    activity_df.reset_index(drop=True, inplace=True)

    st.dataframe(activity_df[["Activity time","User email", "Activity", "Artifact Name"]])


elif selected_value == "recent":
    st.subheader("📌 Most Recently Accessed Artifacts")
    st.info("Displays the most recently accessed reports or datasets. Helps in identifying active artifacts.")
    latest_access1 = latest_access.reset_index(drop=True)
    st.dataframe(latest_access1[["Latest Activity","User email", "Activity", "Artifact Name"]])

elif selected_value == "users":
    st.subheader("📌 Users Activity Status")
    st.info("Shows each user's latest access time and whether they are marked active or inactive.")
    st.dataframe(users_df[["emailAddress", "groupUserAccessRight", "displayName", "workspace_name","activityStatus","Latest Activity Time"]])

elif selected_value == "reports":
    st.subheader("📌 Reports Latest Activity")
    st.info("Details of reports along with their last usage and activity status.")
    st.dataframe(reports_df[["name","Reportstatus Based on Dataset","Activity Status","Latest Artifact Activity"]])

elif selected_value == "datasets":
    st.subheader("📌 Datasets Latest Activity")
    st.info("Displays dataset-level activity insights, freshness status, and usage history.")
    st.dataframe(datasets_df[[ "name","configuredBy","isRefreshable","createdDate","outdated","Dataset Freshness Status","Activity Status","Latest Artifact Activity"]])

elif selected_value == "artifacts":
    st.info("Lists reports and datasets that haven't been accessed at all recently. Useful for cleanup.")

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
st.markdown("""
<div style='text-align: center; font-size: 1.05rem; background-color: #E7DBF3; padding: 14px 24px; border-left: 6px solid #673ab7; border-radius: 8px; margin-bottom: 25px;'>
Use this section to explore detailed actions taken on artifacts such as reports and datasets.
You can filter user activities by date range, artifact name, email, or specific actions like view, edit, or share.
Each activity is grouped and downloadable for further audit or analysis.
</div>
""", unsafe_allow_html=True)

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

    if st.session_state.search_term:
        filtered_df = filtered_df[
            filtered_df["Artifact Name"].str.contains(st.session_state.search_term, case=False, na=False) |
            filtered_df["User email"].str.contains(st.session_state.search_term, case=False, na=False) |
            filtered_df["Activity"].str.contains(st.session_state.search_term, case=False, na=False)
        ]

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

    st.session_state.run_filter = False
    
