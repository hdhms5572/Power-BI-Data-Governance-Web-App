import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Streamlit config
st.set_page_config(page_title="Power BI Workspace Overview", layout="wide")

# Sidebar for credentials
st.sidebar.title("🔐 Power BI API Settings")
access_token = st.sidebar.text_input("Access Token", type="password")
workspace_id = st.sidebar.text_input("Workspace ID", value="1b602ded-5fca-42ed-a4fc-583fdac83a64")

# API call function
def call_powerbi_api(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API call failed: {response.status_code} - {response.text}")
        return None

# Main logic
if access_token and workspace_id:
    # API endpoints
    reports_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
    datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    users_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"

    # Fetch data
    reports_data = call_powerbi_api(reports_url, access_token)
    datasets_data = call_powerbi_api(datasets_url, access_token)
    users_data = call_powerbi_api(users_url, access_token)

    if reports_data and datasets_data and users_data:
        # Create DataFrames
        reports_df = pd.DataFrame(reports_data["value"])
        datasets_df = pd.DataFrame(datasets_data["value"])
        users_df = pd.DataFrame(users_data["value"])

        # Data cleanup
        users_df = users_df.drop(columns=['identifier'], errors='ignore')
        users_df.dropna(subset=['emailAddress'], inplace=True)
        reports_df = reports_df.drop(columns=['subscriptions'], errors='ignore')
        datasets_df = datasets_df.drop(columns=['upstreamDatasets'], errors='ignore')

        # Dataset cleanup and classification
        datasets_df["createdDate"] = pd.to_datetime(datasets_df["createdDate"], errors="coerce").dt.tz_localize(None)
        cutoff = pd.Timestamp.now() - pd.DateOffset(months=12)
        datasets_df["outdated"] = datasets_df["createdDate"] < cutoff
        datasets_df["datasetStatus"] = datasets_df["isRefreshable"].apply(lambda x: "Active" if x else "Inactive")

        # Add dataset attributes to reports
        reports_df = reports_df.merge(
            datasets_df[['id', 'datasetStatus', 'outdated']],
            left_on="datasetId",
            right_on="id",
            how="left"
        )

        def classify_report(row):
            if row['datasetStatus'] == "Inactive":
                return "Inactive"
            elif row['datasetStatus'] == "Active" and row["outdated"]:
                return 'Active (Outdated)'
            elif row['datasetStatus'] == "Active" and not row["outdated"]:
                return 'Active'
            else:
                return 'Unknown'

        reports_df["reportstatus"] = reports_df.apply(classify_report, axis=1)

        # Title
        st.title("📊 Power BI Workspace Overview")

        # DataFrames
        st.subheader("📄 Reports")
        st.dataframe(reports_df)

        st.subheader("📊 Datasets")
        st.dataframe(datasets_df)

        st.subheader("👥 Users")
        st.dataframe(users_df[["displayName", "emailAddress", "groupUserAccessRight", "principalType"]])

        # --- VISUALIZATIONS ---

        # 1. Bar plot of report statuses
        st.subheader("📊 Report Status Count")
        fig1, ax1 = plt.subplots()
        sns.countplot(data=reports_df, x="reportstatus", palette="Set2", ax=ax1)
        ax1.set_title("Number of Reports by Status")
        ax1.set_xlabel("Status")
        ax1.set_ylabel("Count")
        st.pyplot(fig1)

        # 2. Pie chart of report status
        st.subheader("🥧 Report Status Share")
        fig2, ax2 = plt.subplots()
        status_counts = reports_df["reportstatus"].value_counts()
        ax2.pie(status_counts, labels=status_counts.index, autopct="%1.1f%%", colors=sns.color_palette("Set3"), startangle=140)
        ax2.axis("equal")
        st.pyplot(fig2)

        # 3. Stacked bar: Dataset status vs outdated
        st.subheader("📚 Dataset Status vs Freshness")
        grouped = datasets_df.groupby(["datasetStatus", "outdated"]).size().unstack(fill_value=0)
        fig3, ax3 = plt.subplots()
        grouped.plot(kind="bar", stacked=True, ax=ax3, colormap="coolwarm")
        ax3.set_title("Dataset Activity by Freshness")
        ax3.set_ylabel("Count")
        ax3.set_xlabel("Status")
        st.pyplot(fig3)

        # 4. Heatmap of report and dataset status
        st.subheader("🌡️ Report and Dataset Status Heatmap")
        cross = pd.crosstab(reports_df["reportstatus"], reports_df["datasetStatus"])
        fig4, ax4 = plt.subplots()
        sns.heatmap(cross, annot=True, fmt="d", cmap="YlGnBu", ax=ax4)
        ax4.set_title("Report vs Dataset Status")
        st.pyplot(fig4)

        # 5. Histogram: Dataset creation year
        st.subheader("📆 Dataset Creation Year Distribution")
        datasets_df["createdYear"] = datasets_df["createdDate"].dt.year
        fig5, ax5 = plt.subplots()
        sns.histplot(datasets_df["createdYear"].dropna(), bins=range(2015, 2026), kde=False, ax=ax5, color="teal")
        ax5.set_title("Datasets Created by Year")
        ax5.set_xlabel("Year")
        ax5.set_ylabel("Count")
        st.pyplot(fig5)

        # 6. Report Status by Outdated flag
        st.subheader("🕒 Report Freshness Classification")
        fig6, ax6 = plt.subplots()
        sns.countplot(data=reports_df, x="reportstatus", hue="outdated", palette="pastel", ax=ax6)
        ax6.set_title("Report Status by Dataset Freshness")
        ax6.set_xlabel("Report Status")
        ax6.set_ylabel("Count")
        st.pyplot(fig6)

    else:
        st.warning("❌ Could not fetch all data. Please check your token and workspace ID.")
else:
    st.info("🔑 Enter your access token and workspace ID in the sidebar to begin









import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

# Apply sidebar style and show workspace info
apply_sidebar_style()
show_workspace()

st.set_page_config(page_title="Activity Log Insights", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔍 Activity Log Insights</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ✅ Protect page: Require login
if not st.session_state.get("logged_in") or not st.session_state.get("access_token"):
    st.warning("🔒 Please log in from the main page.")
    st.stop()

# ✅ Load credentials
token = st.session_state.access_token
workspace = st.session_state.workspace_id
email = st.session_state.user_email

# ✅ Cache workspace data
@st.cache_data(show_spinner=False)
def load_workspace_data(token, workspace, email):
    return get_filtered_dataframes(token, workspace, email)

reports_df, datasets_df, users_df = load_workspace_data(token, workspace, email)

# ✅ File uploader (disabled if already uploaded)
uploaded_file = st.file_uploader(
    "Upload CSV file...",
    key="activity_upload",
    disabled="uploaded_file_bytes" in st.session_state
)

# ✅ Prevent infinite reruns with a flag
if uploaded_file is not None and not st.session_state.get("file_just_uploaded", False):
    st.session_state["uploaded_file_bytes"] = uploaded_file.read()
    st.session_state["data_processed"] = False
    st.session_state["file_just_uploaded"] = True
    st.rerun()

# ✅ Reset the flag after rerun
if st.session_state.get("file_just_uploaded"):
    st.session_state["file_just_uploaded"] = False

# ✅ Reset uploaded file manually
if "uploaded_file_bytes" in st.session_state:
    st.success("✅ File uploaded successfully.")
    if st.button("🔄 Reset Uploaded File"):
        for key in list(st.session_state.keys()):
            if key.startswith("uploaded_file") or key.endswith("_df") or key in ["data_processed", "file_just_uploaded"]:
                del st.session_state[key]
        st.rerun()

# ✅ Stop if no file
if "uploaded_file_bytes" not in st.session_state:
    st.warning("📂 Please upload a CSV file to proceed.")
    st.stop()

# ✅ Reconstruct DataFrame
file_like = io.BytesIO(st.session_state["uploaded_file_bytes"])
activity_df_raw = pd.read_csv(file_like)

# ✅ Process data once
if not st.session_state.get("data_processed", False):
    with st.spinner("Processing uploaded file..."):
        activity_df = activity_df_raw.copy()
        activity_df2 = activity_df_raw.copy()

        activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
        activity_df = activity_df.sort_values("Activity time")

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

        reports_df["Activity Status"] = reports_df.apply(
            lambda row: "Active" if row["id"] in active_artifact_ids or row["datasetId"] in active_artifact_ids else "Inactive", axis=1)

        datasets_df["Activity Status"] = datasets_df.apply(
            lambda row: "Active" if row["id"] in active_artifact_ids or dataset_to_report_dict.get(row["id"]) in active_artifact_ids else "Inactive", axis=1)

        artifact_activity_map = dict(zip(latest_access1["ArtifactId"], latest_access1["Latest Activity"]))

        reports_df["Latest Artifact Activity"] = reports_df.apply(
            lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(row["datasetId"]), axis=1)

        datasets_df["Latest Artifact Activity"] = datasets_df.apply(
            lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(dataset_to_report_dict.get(row["id"])), axis=1)

        # ✅ Store processed data
    st.session_state["activity_df"] = activity_df
    st.session_state["activity_df2"] = activity_df2
    st.session_state["latest_access1"] = latest_access1
    st.session_state["users_df"] = users_df
    st.session_state["reports_df"] = reports_df
    st.session_state["datasets_df"] = datasets_df
    st.session_state["data_processed"] = True

    # ✅ Load processed data from session state
activity_df = st.session_state.get("activity_df")
activity_df2 = st.session_state.get("activity_df2")
latest_access1 = st.session_state.get("latest_access1")
users_df = st.session_state.get("users_df")
reports_df = st.session_state.get("reports_df")
datasets_df = st.session_state.get("datasets_df")


# ✅ Theme-aware styling
theme_base = st.get_option("theme.base") or "light"
fig_alpha = 1.0 if theme_base == "dark" else 0.01

# ✅ Visualizations
with st.expander("📊 User Insights"):
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Artifact Access Heatmap")
        heatmap_data = activity_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(12, 3))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        ax.set_title("Access Heatmap", color="gray")
        sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax, cbar=False)
        st.pyplot(fig)

    with col2:
        st.subheader("User Activity Status")
        fig, ax = plt.subplots(figsize=(4, 3))
        fig.patch.set_alpha(fig_alpha)
        ax.patch.set_alpha(fig_alpha)
        sns.countplot(data=users_df, x="activityStatus", palette={"Active": "green", "Inactive": "red"}, ax=ax)
        ax.set_title("User Activity", color="gray")
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
        unique_users = unique_users[unique_users['User email'].str.contains("@", na=False)]
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
        ax.title.set_color('gray')
        ax.xaxis.label.set_color('gray')
        ax.yaxis.label.set_color('gray')
        ax.tick_params(colors='gray')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color('gray')
        sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
        ax.set_title("Monthly Usage")
        ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
        st.pyplot(fig)

st.markdown("""<hr style="margin-top:3rem; margin-bottom:2rem;">""", unsafe_allow_html=True)

# ✅ Insight Selector
activity_options = {
    "-- Select an insight --": "None",
    "📁 Activity Log Insights": "activity",
    "📌 Recently Accessed Artifacts": "recent",
    "🧍‍♂️ Users Activity Status": "users",
    "📈 Reports Latest Activity": "reports",
    "🗃️ Datasets Latest Activity": "datasets",
    "📭 Unused Artifacts": "artifacts"
}

selected_key = st.selectbox("🔍 Select insight to explore:", options=list(activity_options.keys()))
selected_value = activity_options[selected_key]

# ✅ Display selected insight
if selected_value == "activity":
    st.subheader("📁 Activity Log Insights")
    st.dataframe(activity_df2)

elif selected_value == "recent":
    st.subheader("📌 Most Recently Accessed Artifacts")
    st.dataframe(latest_access1.reset_index(drop=True))

elif selected_value == "users":
    st.subheader("🧍‍♂️ Users Activity Status")
    st.dataframe(users_df)

elif selected_value == "reports":
    st.subheader("📈 Reports Latest Activity")
    st.dataframe(reports_df[[
        "id", "name", "datasetId", "datasetStatus", "outdated",
        "Reportstatus Based on Dataset", "Activity Status", "Latest Artifact Activity"
    ]])

elif selected_value == "datasets":
    st.subheader("🗃️ Datasets Latest Activity")
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

