import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import  apply_sidebar_style, show_workspace, render_profile_header,get_cached_workspace_data, add_logout_button

def inject_external_style():
    with open("static/style.css") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

for key in ["activity_df", "activity_filename"]:
    if key not in st.session_state:
        st.session_state[key] = None

st.set_page_config(page_title="Top Engagement Insights", layout="wide", page_icon="🏆")
apply_sidebar_style()
add_logout_button()
show_workspace()
inject_external_style()
render_profile_header()

col1, col2, col3 = st.columns(3)
with col2:
    st.image("./images/dover_log.png")

st.markdown("<h1 style='text-align: center;'>🏆 Top Engagement Insights</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; font-size: 1.05rem; background-color: #E7DBF3; padding: 14px 24px; border-left: 6px solid #673ab7; border-radius: 8px; margin-bottom: 25px;'>
This dashboard provides insights into the most actively used <strong>reports</strong>, <strong>datasets</strong>, and <strong>users</strong> across your selected workspaces.
Analyze engagement trends, identify your top content and contributors, and monitor recent activity within the last 3 months.
Use this view to understand usage behavior, improve resource visibility, and guide governance decisions.
</div><hr>
""", unsafe_allow_html=True)


if not (st.session_state.get("access_token") and st.session_state.get("workspace_ids") and st.session_state.get("user_email")):
    st.warning("Missing credentials or workspace selection.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}


reports_df_list, datasets_df_list, users_df_list = [], [], []
for ws_id in workspace_ids:
    reports, datasets, users = get_cached_workspace_data(token, ws_id, email)
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

if st.session_state["activity_df"] is None:
    uploaded_file = st.file_uploader("📤 Upload Activity CSV", type=["csv"])
    if uploaded_file:
        try:
            activity_df = pd.read_csv(uploaded_file)
            if activity_df.empty:
                st.error("❌ Uploaded file is empty.")
                st.stop()
            st.session_state["activity_df"] = activity_df
            st.session_state["activity_filename"] = uploaded_file.name
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to read file: {e}")
            st.stop()
    else:
        st.warning("⚠️ Please upload an activity CSV file to continue.")
        st.stop()
else:
    activity_df = st.session_state["activity_df"]
    st.success(f"✅ Using uploaded file: {st.session_state['activity_filename']}")
    if st.button("🔄 Reset Activity CSV"):
        st.session_state["activity_df"] = None
        st.session_state["activity_filename"] = None
        st.rerun()
# activity_df = handle_activity_upload()
# if activity_df is None or activity_df.empty:
#     st.warning("⚠️ No activity data found. Please upload a valid activity CSV.")
#     st.stop()

# ---- Prepare Activity Data ----
activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
activity_df = activity_df.sort_values("Activity time")

# ---- Latest activity per report or dataset ----
latest_access = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
latest_access.rename(columns={"Activity time": "Latest Activity"}, inplace=True)

# ---- Prepare mappings and recent user activity ----
report_ids = set(reports_df["id"])
dataset_ids = set(datasets_df["id"])
cutoff = pd.Timestamp.now() - pd.DateOffset(months=3)

recent_user_activity = activity_df[activity_df["Activity time"] >= cutoff]
recent_active_users = recent_user_activity["User email"].dropna().unique()

users_df["activityStatus"] = users_df["emailAddress"].apply(
    lambda x: "Active" if x in recent_active_users else "Inactive"
)

# ---- Visualizations ----
col1, col2 = st.columns(2)
standard_color = ["#87CEEB"] * 5  # Sky blue

# 📊 Top 5 Reports
with col1:
    st.markdown("#### 📊 Top Reports")
    top_reports = activity_df[activity_df["ArtifactId"].isin(reports_df["id"])]
    report_usage = top_reports["ArtifactId"].value_counts().head(5).reset_index()
    report_usage.columns = ["Report ID", "Usage Count"]
    report_usage = report_usage.merge(reports_df[["id", "name"]], left_on="Report ID", right_on="id", how="left")

    fig1, ax1 = plt.subplots(figsize=(4, 3))
    sns.barplot(data=report_usage, x="Usage Count", y="name", palette=standard_color, ax=ax1)
    ax1.set_title("Top Reports")
    st.pyplot(fig1)

# 📦 Top 5 Datasets
with col2:
    st.markdown("#### 📦 Top Datasets")
    top_datasets = activity_df[activity_df["ArtifactId"].isin(datasets_df["id"])]
    dataset_usage = top_datasets["ArtifactId"].value_counts().head(5).reset_index()
    dataset_usage.columns = ["Dataset ID", "Usage Count"]
    dataset_usage = dataset_usage.merge(datasets_df[["id", "name"]], left_on="Dataset ID", right_on="id", how="left")

    fig2, ax2 = plt.subplots(figsize=(4, 3))
    sns.barplot(data=dataset_usage, x="Usage Count", y="name", palette=standard_color, ax=ax2)
    ax2.set_title("Top Datasets")
    st.pyplot(fig2)

# 👤 Top 5 Users
col3, col4 = st.columns(2)
with col3:
    st.markdown("#### 👤 Top Users")
    user_activity = activity_df["User email"].value_counts().head(5).reset_index()
    user_activity.columns = ["User Email", "Activity Count"]
    user_activity = user_activity.merge(users_df[["emailAddress", "displayName"]],
                                        left_on="User Email", right_on="emailAddress", how="left")

    fig3, ax3 = plt.subplots(figsize=(4, 3))
    sns.barplot(data=user_activity, x="Activity Count", y="displayName", palette=standard_color, ax=ax3)
    ax3.set_title("Top Users")
    st.pyplot(fig3)

# ⏱️ Recent Activity (Last 3 Months)
with col4:
    st.markdown("#### ⏱️ Recent Active Users (3 Months)")
    recent_activity = activity_df[activity_df["Activity time"] >= cutoff]
    recent_users = recent_activity["User email"].value_counts().head(5).reset_index()
    recent_users.columns = ["User Email", "Activity Count"]
    recent_users = recent_users.merge(users_df[["emailAddress", "displayName"]],
                                      left_on="User Email", right_on="emailAddress", how="left")

    fig4, ax4 = plt.subplots(figsize=(4, 3))
    sns.barplot(data=recent_users, x="Activity Count", y="displayName", palette=standard_color, ax=ax4)
    ax4.set_title("Top Users (3 Months)")
    st.pyplot(fig4)
