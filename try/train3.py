import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import calendar

# Streamlit config
st.set_page_config(page_title="Power BI Workspace Overview", layout="wide")

# Sidebar for credentials
st.sidebar.title("🔐 Power BI API Settings")
access_token = st.sidebar.text_input("Access Token", type="password")
workspace_id = st.sidebar.text_input("Workspace ID", value="cf7a33dd-365c-465d-b3a6-89cd2a3ef08c")
user_email = st.sidebar.text_input("Your Email Address")
page = st.selectbox("What are looking for...", ("Reports", "Datasets", "Users", "Activity Analysis"), index=None, placeholder="Please Select")

# API call function
def call_powerbi_api(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API call failed: {response.status_code} - {response.text}")
        return None

if access_token and workspace_id and user_email:
    # API Endpoints
    reports_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
    datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    users_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"

    # Fetch data
    reports_data = call_powerbi_api(reports_url, access_token)
    datasets_data = call_powerbi_api(datasets_url, access_token)
    users_data = call_powerbi_api(users_url, access_token)

    if reports_data and datasets_data and users_data:
        reports_df = pd.DataFrame(reports_data["value"])
        datasets_df = pd.DataFrame(datasets_data["value"])
        users_df = pd.DataFrame(users_data["value"])

        domain = user_email.split('@')[-1]
        filtered_datasets_df = datasets_df[datasets_df["configuredBy"].str.endswith(domain, na=False)]
        allowed_dataset_ids = set(filtered_datasets_df["id"].tolist())
        filtered_reports_df = reports_df[reports_df["datasetId"].isin(allowed_dataset_ids)]
        filtered_users_df = users_df[users_df.get("emailAddress", "").str.endswith(domain, na=False)]

        filtered_users_df = filtered_users_df.drop(columns=['identifier'], errors='ignore')
        filtered_users_df.dropna(subset=['emailAddress'], inplace=True)
        filtered_datasets_df["createdDate"] = pd.to_datetime(filtered_datasets_df["createdDate"], errors="coerce").dt.tz_localize(None)
        cutoff = pd.Timestamp.now() - pd.DateOffset(months=12)
        filtered_datasets_df["outdated"] = filtered_datasets_df["createdDate"] < cutoff
        filtered_datasets_df["datasetStatus"] = filtered_datasets_df["isRefreshable"].apply(lambda x: "Active" if x else "Inactive")

        filtered_reports_df = filtered_reports_df.merge(
            filtered_datasets_df[['id', 'datasetStatus', 'outdated']],
            left_on="datasetId",
            right_on="id",
            how="left"
        )

        def classify_report(row):
            if row['datasetStatus'] == "Inactive":
                return "Inactive"
            elif row['datasetStatus'] == "Active" and row["outdated"]:
                return 'Active (Outdated)'
            elif row['datasetStatus'] == "Active":
                return 'Active'
            return 'Unknown'

        filtered_reports_df["reportstatus"] = filtered_reports_df.apply(classify_report, axis=1)

        if page == "Reports":
            st.title("📄 Reports")
            st.dataframe(filtered_reports_df)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Report Status Count")
                fig1, ax1 = plt.subplots()
                sns.countplot(data=filtered_reports_df, x="reportstatus", palette={"Active": "green", "Inactive": "red", "Active (Outdated)": "orange"}, ax=ax1)
                st.pyplot(fig1)
            with col2:
                st.subheader("🥧 Report Status Share")
                fig2, ax2 = plt.subplots()
                counts = filtered_reports_df["reportstatus"].value_counts()
                ax2.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=["green", "red", "orange"], startangle=150)
                ax2.axis("equal")
                st.pyplot(fig2)

        elif page == "Datasets":
            st.title("📊 Datasets")
            st.dataframe(filtered_datasets_df)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📓 Dataset Status vs Freshness")
                group = filtered_datasets_df.groupby(["datasetStatus", "outdated"]).size().unstack(fill_value=0)
                fig3, ax3 = plt.subplots()
                group.plot(kind="bar", stacked=True, ax=ax3, colormap="coolwarm")
                st.pyplot(fig3)
            with col2:
                st.subheader("🌡️ Heatmap: Report vs Dataset Status")
                cross = pd.crosstab(filtered_reports_df["reportstatus"], filtered_reports_df["datasetStatus"])
                fig4, ax4 = plt.subplots()
                sns.heatmap(cross, annot=True, fmt="d", cmap="Blues", ax=ax4)
                st.pyplot(fig4)

        elif page == "Users":
            st.title("👥 Users")
            st.dataframe(filtered_users_df[["displayName", "emailAddress", "groupUserAccessRight", "principalType"]])

        elif page == "Activity Analysis":
            # ------------------ Page Setup ------------------
            st.set_page_config(page_title="🔍 Activity Log Insights", layout="wide")
            sns.set_theme(style="whitegrid")  # Seaborn theme
            plt.rcParams["figure.figsize"] = (8, 4)  # Smaller default plot size
            
            # ------------------ Load Data ------------------
            st.title("🔍 Activity Log Insights")
            
            activity_df = pd.read_csv(r"C:\\Users\\10094790\\Downloads\\data.csv")
            st.dataframe(activity_df)
            
            # ------------------ Preprocessing ------------------
            activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
            activity_df = activity_df.sort_values("Activity time")
            
            latest_access1 = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
            latest_access1.rename(columns={"Activity time": "Latest Activity"}, inplace=True)
            
            # ------------------ Artifact Type Classification ------------------
            report_ids = set(reports_df["id"])
            dataset_ids = set(datasets_df["id"])
            
            def classify_artifact_type(artifact_id):
                if artifact_id in report_ids:
                    return "Report"
                elif artifact_id in dataset_ids:
                    return "Dataset"
                return "Unknown"
            
            latest_access1["ArtifactType"] = latest_access1["ArtifactId"].apply(classify_artifact_type)
            
            # ------------------ Recently Accessed Artifacts ------------------
            st.subheader("📌 Most Recently Accessed Artifacts")
            st.dataframe(latest_access1)
            
            # ------------------ User Activity Status ------------------
            active_user_emails = activity_df["User email"].dropna().unique()
            users_df["activityStatus"] = users_df["emailAddress"].apply(
                lambda x: "Active" if x in active_user_emails else "Inactive"
            )
            
            st.subheader("📌 Users Activity Status")
            st.dataframe(users_df)
            
            # ------------------ Artifact Activity Status ------------------
            active_artifact_ids = set(latest_access1["ArtifactId"])
            dataset_to_report_dict = dict(zip(reports_df["datasetId"], reports_df["id"]))
            
            reports_df["activityStatus2"] = reports_df.apply(
                lambda row: "Active" if row["id"] in active_artifact_ids or row["datasetId"] in active_artifact_ids else "Inactive",
                axis=1
            )
            
            datasets_df["activityStatus2"] = datasets_df.apply(
                lambda row: "Active" if row["id"] in active_artifact_ids or dataset_to_report_dict.get(row["id"]) in active_artifact_ids else "Inactive",
                axis=1
            )
            
            # ------------------ Latest Artifact Activity ------------------
            artifact_activity_map = dict(zip(latest_access1["ArtifactId"], latest_access1["Latest Activity"]))
            
            reports_df["Latest Artifact Activity"] = reports_df.apply(
                lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(row["datasetId"]),
                axis=1
            )
            
            datasets_df["Latest Artifact Activity"] = datasets_df.apply(
                lambda row: artifact_activity_map.get(row["id"]) or artifact_activity_map.get(dataset_to_report_dict.get(row["id"])),
                axis=1
            )
            
            st.subheader("📌 Reports Latest Activity")
            st.dataframe(reports_df)
            
            st.subheader("📌 Datasets Latest Activity")
            st.dataframe(datasets_df)
            
            # ------------------ Charts ------------------
            
            # 📊 User Status Count and Artifact Heatmap (side-by-side)
            st.subheader("📊 User Insights")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**User Activity Status**")
                fig, ax = plt.subplots(figsize=(6, 3))
                sns.countplot(data=users_df, x="activityStatus", palette={"Active": "green", "Inactive": "red"}, ax=ax)
                ax.set_title("User Activity")
                st.pyplot(fig)
            
            with col2:
                st.markdown("**Artifact Access Heatmap**")
                heatmap_data = activity_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
                fig, ax = plt.subplots(figsize=(6, 3))
                sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax, cbar=False)
                ax.set_title("Access Heatmap")
                st.pyplot(fig)
            
            # 📈 Top Accessed Reports and Monthly Trend (side-by-side)
            st.subheader("📈 Usage Trends")
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("**Top 10 Accessed Reports**")
                top_reports = activity_df["Artifact Name"].value_counts().head(10).reset_index()
                top_reports.columns = ["Report Name", "Access Count"]
            
                fig, ax = plt.subplots(figsize=(6, 3))
                sns.barplot(data=top_reports, x="Access Count", y="Report Name", palette="crest", ax=ax)
                ax.set_title("Top Reports")
                st.pyplot(fig)
            
            with col4:
                st.markdown("**Monthly Usage Trend**")
                activity_df["YearMonth"] = activity_df["Activity time"].dt.to_period("M").astype(str)
                monthly_usage = activity_df.groupby("YearMonth").size().reset_index(name="Access Count")
                monthly_usage["YearMonth"] = pd.to_datetime(monthly_usage["YearMonth"])
                monthly_usage = monthly_usage.sort_values("YearMonth")
            
                fig, ax = plt.subplots(figsize=(6, 3))
                sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
                ax.set_title("Monthly Usage")
                ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
                st.pyplot(fig)


    else:
        st.warning("❌ Could not fetch all data. Please check your token and workspace ID.")
else:
    st.info("🔑 Enter your access token, email, and workspace ID in the sidebar to begin.")
