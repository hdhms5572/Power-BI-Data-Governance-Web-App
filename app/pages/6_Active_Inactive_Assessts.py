import streamlit as st
import pandas as pd
import plotly.express as px
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace, render_profile_header

# Inject CSS styling
def inject_external_style():
    with open("static/style.css") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Initial Setup
st.set_page_config(page_title="Active vs Inactive Summary", layout="wide", page_icon="📍")
apply_sidebar_style()
show_workspace()
inject_external_style()
render_profile_header()

col1, col2, col3 = st.columns(3)
with col2:
    st.image("./images/dover_log.png")

st.markdown("<h1 style='text-align: center;'>📍 Active vs Inactive Summary</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; font-size: 1.05rem; background-color: #E7DBF3; padding: 14px 24px; border-left: 6px solid #673ab7; border-radius: 8px; margin-bottom: 25px;'>
This dashboard provides a quick summary of active and inactive reports, datasets, and users based on the latest activity logs.
Use this view to identify unused assets, optimize governance, and take cleanup actions.
</div><hr>
""", unsafe_allow_html=True)

# Session Validation
if not (st.session_state.get("access_token") and
        st.session_state.get("workspace_ids") and
        st.session_state.get("user_email")):
    st.warning("❌ Missing access token or selected workspace.")
    st.stop()

# Load session state
token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Workspace selector with "Select All" option
workspace_options = [workspace_map.get(ws, "Unknown") for ws in workspace_ids]
select_all = st.checkbox("✅ Select All Workspaces", value=False)

if select_all:
    selected_ws_names = workspace_options
else:
    selected_ws_names = st.multiselect("🔀 Choose Workspaces", options=workspace_options)

if not selected_ws_names:
    st.info("👆 Please select one or more workspaces to begin.")
    st.stop()

# Get workspace IDs from selected names
selected_ws_ids = [k for k, v in workspace_map.items() if v in selected_ws_names]

# Load data from selected workspaces
reports_df_list, datasets_df_list, users_df_list = [], [], []
for ws_id in selected_ws_ids:
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

# Load Activity CSV
activity_df = pd.read_csv("./sample_analysis/data.csv")
activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
activity_df = activity_df.sort_values("Activity time")

# Filter activity only for selected workspace artifacts
workspace_artifact_ids = set(reports_df["id"]).union(set(datasets_df["id"]))
activity_df = activity_df[activity_df["ArtifactId"].isin(workspace_artifact_ids)]

# Analyze activity
cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=3)
latest_access = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
recent_user_activity = activity_df[activity_df["Activity time"] >= cutoff_date]
recent_users = recent_user_activity["User email"].dropna().unique()
recent_artifacts = latest_access["ArtifactId"].unique()

# Classify active/inactive
users_df["activityStatus"] = users_df["emailAddress"].apply(lambda x: "Active" if x in recent_users else "Inactive")
reports_df["Activity Status"] = reports_df["id"].apply(lambda x: "Active" if x in recent_artifacts else "Inactive")
datasets_df["Activity Status"] = datasets_df["id"].apply(lambda x: "Active" if x in recent_artifacts else "Inactive")

# Summary KPIs
st.markdown("### 📊 Summary KPIs")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Active Reports", (reports_df["Activity Status"] == "Active").sum())
    st.metric("Inactive Reports", (reports_df["Activity Status"] == "Inactive").sum())

with col2:
    st.metric("Active Datasets", (datasets_df["Activity Status"] == "Active").sum())
    st.metric("Inactive Datasets", (datasets_df["Activity Status"] == "Inactive").sum())

with col3:
    st.metric("Active Users", (users_df["activityStatus"] == "Active").sum())
    st.metric("Inactive Users", (users_df["activityStatus"] == "Inactive").sum())

st.markdown("---")

# Plotly Donut Charts
st.markdown("###  Interactive Activity Distribution")
col4, col5, col6 = st.columns(3)

def plot_donut(data, label, color1="#0A6EBD", color2="#274472"):
    counts = data.value_counts().reset_index()
    counts.columns = [label, "Count"]
    fig = px.pie(
        counts, values="Count", names=label,
        hole=0.5,
        color=label,
        color_discrete_map={"Active": color1, "Inactive": color2}
    )
    fig.update_traces(textinfo="percent+label", hoverinfo="label+value+percent", pull=[0.05, 0])
    fig.update_layout(title=f"{label} Status Distribution", showlegend=True)
    return fig

with col4:
    st.plotly_chart(plot_donut(reports_df["Activity Status"], "Reports"), use_container_width=True)
with col5:
    st.plotly_chart(plot_donut(datasets_df["Activity Status"], "Datasets"), use_container_width=True)
with col6:
    st.plotly_chart(plot_donut(users_df["activityStatus"], "Users"), use_container_width=True)

st.markdown("---")

# Data Explorer
st.markdown("### 🔍 View Detailed Tables")

option = st.selectbox("Choose an asset group to explore:", [
    "-- Select --", "Active Reports", "Inactive Reports",
    "Active Datasets", "Inactive Datasets",
    "Active Users", "Inactive Users"
])

if option == "Active Reports":
    st.dataframe(reports_df[reports_df["Activity Status"] == "Active"][["name", "workspace_name", "webUrl"]])
elif option == "Inactive Reports":
    st.dataframe(reports_df[reports_df["Activity Status"] == "Inactive"][["name", "workspace_name", "webUrl"]])
elif option == "Active Datasets":
    st.dataframe(datasets_df[datasets_df["Activity Status"] == "Active"][["name", "workspace_name", "webUrl"]])
elif option == "Inactive Datasets":
    st.dataframe(datasets_df[datasets_df["Activity Status"] == "Inactive"][["name", "workspace_name", "webUrl"]])
elif option == "Active Users":
    st.dataframe(users_df[users_df["activityStatus"] == "Active"][["displayName", "emailAddress", "workspace_name"]])
elif option == "Inactive Users":
    st.dataframe(users_df[users_df["activityStatus"] == "Inactive"][["displayName", "emailAddress", "workspace_name"]])