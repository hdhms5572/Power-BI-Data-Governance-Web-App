import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

def inject_external_style():
    with open("static/style.css") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Setup
st.set_page_config(page_title="Top Engagement Insights", layout="wide", page_icon="🏆")
apply_sidebar_style()
show_workspace()
inject_external_style()

st.markdown("<h2 style='text-align: center;'>🏆 Top Engagement Insights</h2><hr>", unsafe_allow_html=True)

# --- Session Check ---
if not (st.session_state.get("access_token") and
        st.session_state.get("workspace_ids") and
        st.session_state.get("user_email")):
    st.warning("Missing credentials or workspace selection.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Load data 
reports_df_list, datasets_df_list, users_df_list = [], [], []
for ws_id in workspace_ids:
    reports, datasets, users = get_filtered_dataframes(token, ws_id, email)
    ws_name = workspace_map.get(ws_id, "Unknown")
    for df in [reports, datasets, users]:
        df["workspace_id"] = ws_id
        df["workspace_name"] = ws_name
    reports_df_list.append(reports)
    datasets_df_list.append(datasets)
    users_df_list.append(users)

reports_df = pd.concat(reports_df_list, ignore_index=True)
datasets_df = pd.concat(datasets_df_list, ignore_index=True)
users_df = pd.concat(users_df_list, ignore_index=True)

# Adjust if different
activity_path = r"sample_analysis/data.csv"
activity_df = pd.read_csv(activity_path)
activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
activity_df = activity_df.sort_values("Activity time")

# Latest activity per report or dataset
latest_access = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
latest_access.rename(columns={"Activity time": "Latest Activity"}, inplace=True)

# Prepare active mappings
report_ids = set(reports_df["id"])
dataset_ids = set(datasets_df["id"])
dataset_to_report = dict(zip(reports_df["datasetId"], reports_df["id"]))
active_users = activity_df["User email"].dropna().unique()
cutoff = pd.Timestamp.now() - pd.DateOffset(months=3)
recent_user_activity = activity_df[activity_df["Activity time"] >= cutoff]
recent_active_users = recent_user_activity["User email"].dropna().unique()

users_df["activityStatus"] = users_df["emailAddress"].apply(lambda x: "Active" if x in recent_active_users else "Inactive")

# --- Visualizations ---
fig_alpha = 1.0 if st.get_option("theme.base") == "dark" else 0.01

col1, col2 = st.columns(2)

# Top 5 Reports
with col1:
    st.markdown("#### 📊 Top Reports")
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

# Top 5 Datasets
with col2:
    st.markdown("#### 📦 Top Datasets")
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

# Top 5 Users
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### 👤 Top Users")
    user_activity = activity_df["User email"].value_counts().head(5).reset_index()
    user_activity.columns = ["User Email", "Activity Count"]
    user_activity = user_activity.merge(users_df[["emailAddress", "displayName"]],
                                        left_on="User Email", right_on="emailAddress", how="left")

    fig3, ax3 = plt.subplots(figsize=(4, 3))
    fig3.patch.set_alpha(fig_alpha)
    ax3.patch.set_alpha(fig_alpha)
    sns.barplot(data=user_activity, x="Activity Count", y="displayName", palette="Blues_d", ax=ax3)
    ax3.set_title("Top Users", color="gray")
    ax3.tick_params(colors='gray')
    for label in ax3.get_xticklabels() + ax3.get_yticklabels():
        label.set_color("gray")
    st.pyplot(fig3)

# Recent Activity (Last 3 Months)
with col4:
    st.markdown("#### ⏱️ Recent Active Users (3 Months)")
    recent_activity = activity_df[activity_df["Activity time"] >= cutoff]
    recent_users = recent_activity["User email"].value_counts().head(5).reset_index()
    recent_users.columns = ["User Email", "Activity Count"]
    recent_users = recent_users.merge(users_df[["emailAddress", "displayName"]],
                                      left_on="User Email", right_on="emailAddress", how="left")

    fig4, ax4 = plt.subplots(figsize=(4, 3))
    fig4.patch.set_alpha(fig_alpha)
    ax4.patch.set_alpha(fig_alpha)
    sns.barplot(data=recent_users, x="Activity Count", y="displayName", palette="Purples", ax=ax4)
    ax4.set_title("Top Users (3 Months)", color="gray")
    ax4.tick_params(colors='gray')
    for label in ax4.get_xticklabels() + ax4.get_yticklabels():
        label.set_color("gray")
    st.pyplot(fig4)
