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
    st.info("🔑 Enter your access token and workspace ID in the sidebar to begin.")
