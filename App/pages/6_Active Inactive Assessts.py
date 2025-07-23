import streamlit as st
import pandas as pd
import plotly.express as px
from utils import  apply_sidebar_style, show_workspace, render_profile_header
from utils import handle_activity_upload,validate_session,apply_activity_status
from utils import get_cached_workspace_data, add_logout_button

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

st.set_page_config(page_title="Active vs Inactive Summary", layout="wide", page_icon="📍")

col1, col2, col3 = st.columns(3)
with col2:
    st.image("./images/dover_log.png")

st.markdown("""
<h1 style='text-align: center;'>📍 Active vs Inactive Summary</h1>
<div style='text-align: center; font-size: 1.05rem; background-color: #E7DBF3; padding: 14px 24px; border-left: 6px solid #673ab7; border-radius: 8px; margin-bottom: 25px;'>
This dashboard provides a quick summary of active and inactive reports, datasets, and users based on the latest activity logs.
Select the workspaces you want to analyze and click "View Summary" to load insights.
</div><hr>
""", unsafe_allow_html=True)


if "last_selected_ws" not in st.session_state:
    st.session_state.last_selected_ws = []
if "select_all_toggle" not in st.session_state:
    st.session_state.select_all_toggle = False
if "view_summary_clicked" not in st.session_state:
    st.session_state.view_summary_clicked = False

workspace_ids = st.session_state.workspace_ids
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}
workspace_names = [workspace_map.get(ws, "Unknown") for ws in workspace_ids]

current_toggle = st.checkbox("✅ Select All Workspaces", value=st.session_state.select_all_toggle)
if current_toggle != st.session_state.select_all_toggle:
    st.session_state.select_all_toggle = current_toggle
    st.session_state.last_selected_ws = workspace_names if current_toggle else []
    st.session_state.view_summary_clicked = False
valid_defaults = [ws for ws in st.session_state.get("last_selected_ws", []) if ws in workspace_names]

selected_ws_names = st.multiselect(
    "🔀 Choose Workspaces",
    options=workspace_names,
    default=valid_defaults,
    key="ws_selector"
)


if sorted(selected_ws_names) != sorted(st.session_state.last_selected_ws):
    st.session_state.view_summary_clicked = False
    st.session_state.last_selected_ws = selected_ws_names

if selected_ws_names:
    st.markdown("**Selected Workspaces:**")
    for name in selected_ws_names:
        st.markdown(f"<span style='display:inline-block; background:#e0e0e0; padding:4px 10px; border-radius:15px; margin:2px'>{name}</span>", unsafe_allow_html=True)

if selected_ws_names and not st.session_state.view_summary_clicked:
    if st.button("📊 View Summary"):
        st.session_state.view_summary_clicked = True
    else:
        st.stop()

# if "activity_df" not in st.session_state:
#     uploaded_file = st.file_uploader("📄 Upload Activity CSV", type=["csv"])
#     if uploaded_file is not None:
#         try:
#             st.session_state.activity_df = pd.read_csv(uploaded_file)
#             st.session_state.activity_filename = uploaded_file.name
#             st.rerun()
#         except Exception as e:
#             st.error(f"❌ Error reading uploaded file: {e}")
#             st.stop()
#     else:
#         st.warning("Please upload an activity CSV file to proceed.")
#         st.stop()
# else:
#     st.success(f"✅ Uploaded: {st.session_state.activity_filename}")
#     if st.button("🔄 Reset Activity CSV"):
#         del st.session_state["activity_df"]
#         del st.session_state["activity_filename"]
#         st.rerun()

# activity_df = st.session_state.activity_df
# activity_df = handle_activity_upload()



reports_df_list, datasets_df_list, users_df_list = [], [], []
token = st.session_state.access_token
email = st.session_state.user_email
selected_ws_ids = [k for k, v in workspace_map.items() if v in selected_ws_names]
for ws_id in selected_ws_ids:

    reports, datasets, users = get_cached_workspace_data(token, ws_id, email)
    workspace_name = workspace_map.get(ws_id, "Unknown")
    for df in [reports, datasets, users]:
        df["workspace_id"] = ws_id
        df["workspace_name"] = workspace_name
    reports_df_list.append(reports)
    datasets_df_list.append(datasets)
    users_df_list.append(users)

if not reports_df_list or not datasets_df_list or not users_df_list:
    st.warning("⚠️ No data available for the selected workspace(s). Please try again.")
    st.stop()

reports_df = pd.concat(reports_df_list, ignore_index=True)
datasets_df = pd.concat(datasets_df_list, ignore_index=True)
users_df = pd.concat(users_df_list, ignore_index=True)

#reports_df, datasets_df, users_df = get_combined_workspace_data()
activity_df = handle_activity_upload()
if activity_df is None or activity_df.empty:
    st.warning("⚠️ No activity data found. Please upload a valid activity CSV.")
    st.stop()


activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
activity_df = activity_df.sort_values("Activity time")

workspace_artifact_ids = set(reports_df["id"]).union(set(datasets_df["id"]))
activity_df = activity_df[activity_df["ArtifactId"].isin(workspace_artifact_ids)]

cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=3)
latest_access = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
recent_user_activity = activity_df[activity_df["Activity time"] >= cutoff_date]
recent_users = recent_user_activity["User email"].dropna().unique()
recent_artifacts = latest_access["ArtifactId"].unique()

users_df["activityStatus"] = users_df["emailAddress"].apply(lambda x: "Active" if x in recent_users else "Inactive")
reports_df["Activity Status"] = reports_df["id"].apply(lambda x: "Active" if x in recent_artifacts else "Inactive")
datasets_df["Activity Status"] = datasets_df["id"].apply(lambda x: "Active" if x in recent_artifacts else "Inactive")

k1, k2, k3 = st.columns(3)
with k1:
    st.metric("Active Reports", (reports_df["Activity Status"] == "Active").sum())
    st.metric("Inactive Reports", (reports_df["Activity Status"] == "Inactive").sum())
with k2:
    st.metric("Active Datasets", (datasets_df["Activity Status"] == "Active").sum())
    st.metric("Inactive Datasets", (datasets_df["Activity Status"] == "Inactive").sum())
with k3:
    st.metric("Active Users", (users_df["activityStatus"] == "Active").sum())
    st.metric("Inactive Users", (users_df["activityStatus"] == "Inactive").sum())

st.markdown("### Activity Distribution")
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
    st.dataframe(users_df[users_df["activityStatus"] == "Active"]["displayName emailAddress workspace_name".split()])
elif option == "Inactive Users":
    st.dataframe(users_df[users_df["activityStatus"] == "Inactive"]["displayName emailAddress workspace_name".split()])
