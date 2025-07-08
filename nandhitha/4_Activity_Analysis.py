import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

# ─── Setup ───
apply_sidebar_style()
show_workspace()
st.set_page_config(page_title="Activity Log Insights", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔍 Activity Log Insights</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ─── Authentication ───
if not st.session_state.get("logged_in") or not st.session_state.get("access_token"):
    st.warning("🔒 Please log in from the main page.")
    st.stop()

token = st.session_state.access_token
workspace = st.session_state.workspace_id
email = st.session_state.user_email

@st.cache_data(show_spinner=False)
def load_workspace_data(token, workspace, email):
    return get_filtered_dataframes(token, workspace, email)

reports_df, datasets_df, users_df = load_workspace_data(token, workspace, email)

# ─── File Upload ───
if "uploaded_file_bytes" not in st.session_state:
    uploaded_file = st.file_uploader("Upload CSV file...", key="activity_upload")
    if uploaded_file:
        st.session_state["uploaded_file_bytes"] = uploaded_file.read()
        st.session_state["data_processed"] = False
        st.rerun()
else:
    st.success("✅ File uploaded successfully.")

if st.button("🔁 Refresh Uploaded File"):
    for key in list(st.session_state.keys()):
        if key.startswith("uploaded_file") or key.endswith("_df") or key in ["data_processed"]:
            del st.session_state[key]
    st.rerun()

if "uploaded_file_bytes" not in st.session_state:
    st.warning("📂 Please upload a CSV file to proceed.")
    st.stop()

# ─── Process Uploaded CSV ───
if not st.session_state.get("data_processed", False):
    file_like = io.BytesIO(st.session_state["uploaded_file_bytes"])
    activity_df_raw = pd.read_csv(file_like)

    activity_df = activity_df_raw.copy()
    activity_df2 = activity_df_raw.copy()
    activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
    activity_df = activity_df.sort_values("Activity time")
    activity_df2["Activity time"] = pd.to_datetime(activity_df2["Activity time"], errors="coerce")  # Fix .dt error

    latest_access1 = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
    latest_access1.rename(columns={"Activity time": "Latest Activity"}, inplace=True)

    cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=3)
    recent_user_activity = activity_df[activity_df["Activity time"] >= cutoff_date]
    active_users = recent_user_activity["User email"].dropna().unique()
    users_df["activityStatus"] = users_df["emailAddress"].apply(
        lambda x: "Active" if x in active_users else "Inactive"
    )

    active_artifact_ids = set(latest_access1["ArtifactId"])
    dataset_to_report_dict = dict(zip(reports_df["datasetId"], reports_df["id"]))
    artifact_activity_map = dict(zip(latest_access1["ArtifactId"], latest_access1["Latest Activity"]))

    reports_df["Activity Status"] = reports_df.apply(
        lambda row: "Active" if row["id"] in active_artifact_ids or row["datasetId"] in active_artifact_ids else "Inactive", axis=1)
    reports_df["Latest Artifact Activity"] = reports_df.apply(
        lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(row["datasetId"]), axis=1)

    datasets_df["Activity Status"] = datasets_df.apply(
        lambda row: "Active" if row["id"] in active_artifact_ids or dataset_to_report_dict.get(row["id"]) in active_artifact_ids else "Inactive", axis=1)
    datasets_df["Latest Artifact Activity"] = datasets_df.apply(
        lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(dataset_to_report_dict.get(row["id"])), axis=1)

    st.session_state["activity_df2"] = activity_df2
    st.session_state["latest_access1"] = latest_access1
    st.session_state["reports_df"] = reports_df
    st.session_state["datasets_df"] = datasets_df
    st.session_state["users_df"] = users_df
    st.session_state["data_processed"] = True

# ─── Load Session Data ───
activity_df = st.session_state["activity_df2"]
latest_access1 = st.session_state["latest_access1"]
reports_df = st.session_state["reports_df"]
datasets_df = st.session_state["datasets_df"]
users_df = st.session_state["users_df"]

# ─── Theme-based Styling ───
theme_base = st.get_option("theme.base") or "light"
fig_alpha = 1.0 if theme_base == "dark" else 0.01

# ─── Visualizations ───
with st.expander("📊 User Insights", expanded=True):
    col1, col2 = st.columns([2,1])
    with col1:
        st.subheader("Artifact Access Heatmap")
        heatmap_data = activity_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(12, 3))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax, cbar=False)
        ax.set_title("Access Heatmap", color="gray")
        ax.tick_params(colors='gray')
        ax.xaxis.label.set_color('gray')
        ax.yaxis.label.set_color('gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color('gray')
        st.pyplot(fig)
    with col2:
        st.subheader("User Activity Status")
        fig, ax = plt.subplots(figsize=(4, 3))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        sns.countplot(data=users_df, x="activityStatus", palette={"Active": "green", "Inactive": "red"}, ax=ax)
        ax.set_title("User Activity", color="gray")
        ax.tick_params(colors='gray')
        ax.xaxis.label.set_color('gray')
        ax.yaxis.label.set_color('gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color('gray')
        st.pyplot(fig)

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
        st.pyplot(fig)
    with col4:
        st.subheader("Usage Trends By Opcos")
        unique_users = activity_df.drop_duplicates(subset='User email')
        unique_users['domain'] = unique_users['User email'].str.split('@').str[1]
        domain_counts = unique_users['domain'].value_counts()
        fig, ax = plt.subplots(figsize=(7, 2))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        ax.bar(domain_counts.index, domain_counts.values, color='skyblue')
        ax.set_title('Users per Opcos', color="gray")
        ax.set_xlabel('Email Domain', color="gray")
        ax.set_ylabel('Number of Users', color="gray")
        ax.tick_params(axis='x', rotation=45, colors='gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color('gray')
        st.pyplot(fig)

with st.expander("📅 Weekly and Monthly Access Patterns"):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📆 Weekday Activity")
        activity_df["Weekday"] = activity_df["Activity time"].dt.day_name()
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_counts = activity_df["Weekday"].value_counts().reindex(weekday_order)
        fig, ax = plt.subplots(figsize=(6, 3))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        ax.plot(weekday_counts.index, weekday_counts.values, marker='o', linestyle='-', color='orange')
        ax.set_title("Weekday Activity", color="gray")
        ax.set_xlabel("Day", color="gray")
        ax.set_ylabel("Activity Count", color="gray")
        ax.tick_params(colors='gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color("gray")
        st.pyplot(fig)

    with col2:
        st.subheader("Monthly Usage Trend")
        activity_df["YearMonth"] = activity_df["Activity time"].dt.to_period("M").astype(str)
        monthly_usage = activity_df.groupby("YearMonth").size().reset_index(name="Access Count")
        monthly_usage["YearMonth"] = pd.to_datetime(monthly_usage["YearMonth"])
        monthly_usage = monthly_usage.sort_values("YearMonth")
        fig, ax = plt.subplots(figsize=(6, 2))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        ax.set_title("Monthly Usage", color="gray")
        ax.set_xlabel("Month", color="gray")
        ax.set_ylabel("Access Count", color="gray")
        ax.tick_params(colors='gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color("gray")
        sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
        ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
        st.pyplot(fig)

st.markdown("""<hr style="margin-top:2rem; margin-bottom:1rem;">""", unsafe_allow_html=True)

# ─── Insight Selector ───
activity_options = {
    "-- Select an insight --": None,
    "📁 Activity Log Insights": "activity",
    "📌 Recently Accessed Artifacts": "recent",
    "🧍‍♂️ Users Activity Status": "users",
    "📈 Reports Latest Activity": "reports",
    "🗃️ Datasets Latest Activity": "datasets",
    "📭 Unused Artifacts": "artifacts"
}

selected_key = st.selectbox("🔍 Select insight to explore:", options=list(activity_options.keys()))
selected_value = activity_options[selected_key]

# ─── Table Output ───
if selected_value == "activity":
    st.subheader("📁 Activity Log Insights")
    st.dataframe(activity_df[["Activity time", "User email","Activity","ArtifactId","Artifact Name"]])



elif selected_value == "recent":
    st.subheader("📌 Most Recently Accessed Artifacts")
    st.dataframe(latest_access1.reset_index(drop=True), use_container_width=True)

elif selected_value == "users":
    st.subheader("🧍‍♂️ Users Activity Status")
    st.dataframe(users_df, use_container_width=True)

elif selected_value == "reports":
    st.subheader("📈 Reports Latest Activity")
    st.dataframe(reports_df[[
        "id", "name", "datasetId", "Activity Status", "Latest Artifact Activity"
    ]], use_container_width=True)

elif selected_value == "datasets":
    st.subheader("🗃️ Datasets Latest Activity")
    st.dataframe(datasets_df, use_container_width=True)

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

