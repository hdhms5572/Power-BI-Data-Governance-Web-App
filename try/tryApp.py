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
workspace_id = st.sidebar.text_input("Workspace ID", value="d459e975-fd2e-4db5-a602-03f515215de2")
user_email = st.sidebar.text_input("Your Email Address")

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

        # RLS Filtering: based on email domain
        domain = user_email.split('@')[-1]
        filtered_datasets_df = datasets_df[datasets_df["configuredBy"].str.endswith(domain, na=False)]
        allowed_dataset_ids = filtered_datasets_df["id"].tolist()
        filtered_reports_df = reports_df[reports_df["datasetId"].isin(allowed_dataset_ids)]
        filtered_users_df = users_df[users_df.get("emailAddress", "").str.endswith(domain, na=False)]

        # Cleanup
        filtered_users_df = filtered_users_df.drop(columns=['identifier'], errors='ignore')
        filtered_users_df.dropna(subset=['emailAddress'], inplace=True)
        filtered_datasets_df["createdDate"] = pd.to_datetime(filtered_datasets_df["createdDate"], errors="coerce").dt.tz_localize(None)
        cutoff = pd.Timestamp.now() - pd.DateOffset(months=12)
        filtered_datasets_df["outdated"] = filtered_datasets_df["createdDate"] < cutoff
        filtered_datasets_df["datasetStatus"] = filtered_datasets_df["isRefreshable"].apply(lambda x: "Active" if x else "Inactive")

        # Merge status into reports
        filtered_reports_df = filtered_reports_df.merge(
            filtered_datasets_df[['id', 'datasetStatus', 'outdated']],
            left_on="datasetId",
            right_on="id",
            how="left"
        )

        # Report classification
        def classify_report(row):
            if row['datasetStatus'] == "Inactive":
                return "Inactive"
            elif row['datasetStatus'] == "Active" and row["outdated"]:
                return 'Active (Outdated)'
            elif row['datasetStatus'] == "Active":
                return 'Active'
            return 'Unknown'

        filtered_reports_df["reportstatus"] = filtered_reports_df.apply(classify_report, axis=1)

        # Display
        st.title("🔒 Power BI Workspace Overview (Restricted by Email Domain)")

        st.subheader("📄 Reports")
        st.dataframe(filtered_reports_df)

        st.subheader("📊 Datasets")
        st.dataframe(filtered_datasets_df)

        st.subheader("👥 Users")
        st.dataframe(filtered_users_df[["displayName", "emailAddress", "groupUserAccessRight", "principalType"]])

        # --- VISUALIZATIONS ---
        sns.set_style("whitegrid")

        # Layout in columns
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Report Status Count")
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            sns.countplot(data=filtered_reports_df, x="reportstatus", palette={"Active": "green", "Inactive": "red", "Active (Outdated)": "orange"}, ax=ax1)
            ax1.set_title("Reports by Status")
            ax1.set_xlabel("Status")
            ax1.set_ylabel("Count")
            st.pyplot(fig1)

        with col2:
            st.subheader("🥧 Report Status Share")
            fig2, ax2 = plt.subplots(figsize=(5, 5))
            counts = filtered_reports_df["reportstatus"].value_counts()
            ax2.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=["green", "red", "orange"], startangle=150)
            ax2.axis("equal")
            st.pyplot(fig2)

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("📚 Dataset Status vs Freshness")
            group = filtered_datasets_df.groupby(["datasetStatus", "outdated"]).size().unstack(fill_value=0)
            fig3, ax3 = plt.subplots(figsize=(6, 4))
            group.plot(kind="bar", stacked=True, ax=ax3, colormap="coolwarm")
            ax3.set_title("Dataset Activity by Freshness")
            ax3.set_ylabel("Count")
            ax3.set_xlabel("Status")
            st.pyplot(fig3)

        with col4:
            st.subheader("🌡️ Heatmap: Report vs Dataset Status")
            cross = pd.crosstab(filtered_reports_df["reportstatus"], filtered_reports_df["datasetStatus"])
            fig4, ax4 = plt.subplots(figsize=(6, 4))
            sns.heatmap(cross, annot=True, fmt="d", cmap="Blues", ax=ax4)
            ax4.set_title("Heatmap: Reports vs Dataset Status")
            st.pyplot(fig4)

        st.subheader("📆 Dataset Creation Year Distribution")
        fig5, ax5 = plt.subplots(figsize=(12, 3))
        filtered_datasets_df["createdYear"] = filtered_datasets_df["createdDate"].dt.year
        sns.histplot(filtered_datasets_df["createdYear"].dropna(), bins=range(2015, 2026), kde=False, ax=ax5, color="#4C72B0")
        ax5.set_title("Dataset Created by Year")
        ax5.set_xlabel("Year")
        ax5.set_ylabel("Count")
        st.pyplot(fig5)

        st.subheader("🕒 Report Freshness Classification")
        fig6, ax6 = plt.subplots(figsize=(8, 4))
        sns.countplot(data=filtered_reports_df, x="reportstatus", hue="outdated", palette={True: "orange", False: "green"}, ax=ax6)
        ax6.set_title("Report Status vs Dataset Freshness")
        ax6.set_xlabel("Report Status")
        ax6.set_ylabel("Count")
        st.pyplot(fig6)

    else:
        st.warning("❌ Could not fetch all data. Please check your token and workspace ID.")
else:
    st.info("🔑 Enter your access token, email, and workspace ID in the sidebar to begin.")
