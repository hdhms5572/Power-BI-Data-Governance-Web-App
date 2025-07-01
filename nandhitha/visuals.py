# modules/visuals.py
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from modules.utils import classify_artifact_type

def render_reports_page(filtered_reports_df):
    st.title("📄 Reports Overview")
    st.dataframe(filtered_reports_df)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Report Status Count")
        fig, ax = plt.subplots()
        sns.countplot(data=filtered_reports_df, x="reportstatus",
                      palette={"Active": "green", "Inactive": "red", "Active (Outdated)": "orange"}, ax=ax)
        st.pyplot(fig)

    with col2:
        st.subheader("🥧 Report Status Share")
        counts = filtered_reports_df["reportstatus"].value_counts()
        fig, ax = plt.subplots()
        ax.pie(counts, labels=counts.index, autopct="%1.1f%%",
               colors=["green", "red", "orange"], startangle=150)
        ax.axis("equal")
        st.pyplot(fig)

def render_datasets_page(filtered_datasets_df, filtered_reports_df):
    st.title("📊 Datasets Overview")
    st.dataframe(filtered_datasets_df)

    col1, col2 = st.columns(2)

    if not filtered_datasets_df.empty:
        with col1:
            st.subheader("📚 Dataset Status vs Freshness")
            group = filtered_datasets_df.groupby(["datasetStatus", "outdated"]).size().unstack(fill_value=0)
            fig, ax = plt.subplots()
            group.plot(kind="bar", stacked=True, ax=ax, colormap="coolwarm")
            ax.set_title("Dataset Activity by Freshness")
            st.pyplot(fig)

    if not filtered_reports_df.empty:
        with col2:
            st.subheader("🌡️ Heatmap: Report vs Dataset Status")
            cross = pd.crosstab(filtered_reports_df["reportstatus"], filtered_reports_df["datasetStatus"])
            fig, ax = plt.subplots()
            sns.heatmap(cross, annot=True, fmt="d", cmap="Blues", ax=ax)
            st.pyplot(fig)

    st.subheader("📆 Dataset Creation Year Distribution")
    fig, ax = plt.subplots(figsize=(12, 3))
    filtered_datasets_df["createdYear"] = filtered_datasets_df["createdDate"].dt.year
    sns.histplot(filtered_datasets_df["createdYear"].dropna(), bins=range(2015, 2026), ax=ax, color="#4C72B0")
    ax.set_title("Dataset Created by Year")
    st.pyplot(fig)

def render_users_page(filtered_users_df):
    st.title("👥 Users Overview")
    st.dataframe(filtered_users_df[["displayName", "emailAddress", "groupUserAccessRight", "principalType"]])

def render_activity_page(filtered_users_df, filtered_datasets_df, filtered_reports_df, domain):
    st.title("🔍 Activity Log Insights")
    activity_data = st.file_uploader("Upload activity CSV file")
    if not activity_data:
        return

    activity_df = pd.read_csv(activity_data)
    filtered_activity_df = activity_df[activity_df.get("User email", "").str.endswith(domain, na=False)].copy()
    st.dataframe(filtered_activity_df)

    filtered_activity_df["Activity time"] = pd.to_datetime(filtered_activity_df["Activity time"], errors="coerce")
    filtered_activity_df = filtered_activity_df.sort_values("Activity time")

    latest_access = filtered_activity_df.drop_duplicates(subset="Artifact Name", keep="last")
    latest_access.rename(columns={"Activity time": "Latest Activity"}, inplace=True)

    report_ids = set(filtered_reports_df["id"])
    dataset_ids = set(filtered_datasets_df["id"])

    latest_access["ArtifactType"] = latest_access["ArtifactId"].apply(lambda aid: classify_artifact_type(aid, report_ids, dataset_ids))
    st.subheader("📌 Most Recently Accessed Artifacts")
    st.dataframe(latest_access)

    # User Activity
    active_user_emails = filtered_activity_df["User email"].dropna().unique()
    filtered_users_df["activityStatus"] = filtered_users_df["emailAddress"].apply(
        lambda x: "Active" if x in active_user_emails else "Inactive")
    st.subheader("📌 Users Activity Status")
    st.dataframe(filtered_users_df)

    # Artifact Activity
    active_artifact_ids = set(latest_access["ArtifactId"])
    dataset_to_report = dict(zip(filtered_reports_df["datasetId"], filtered_reports_df["id"]))

    filtered_reports_df["activityStatus2"] = filtered_reports_df.apply(
        lambda row: "Active" if row["id"] in active_artifact_ids or row["datasetId"] in active_artifact_ids else "Inactive",
        axis=1)

    filtered_datasets_df["activityStatus2"] = filtered_datasets_df.apply(
        lambda row: "Active" if row["id"] in active_artifact_ids or dataset_to_report.get(row["id"]) in active_artifact_ids else "Inactive",
        axis=1)

    # Latest activity
    artifact_map = dict(zip(latest_access["ArtifactId"], latest_access["Latest Activity"]))

    filtered_reports_df["Latest Artifact Activity"] = filtered_reports_df.apply(
        lambda row: artifact_map.get(row["id"]) or artifact_map.get(row["datasetId"]), axis=1)
    filtered_datasets_df["Latest Artifact Activity"] = filtered_datasets_df.apply(
        lambda row: artifact_map.get(row["id"]) or artifact_map.get(dataset_to_report.get(row["id"])), axis=1)

    st.subheader("📌 Reports Latest Activity")
    st.dataframe(filtered_reports_df)

    st.subheader("📌 Datasets Latest Activity")
    st.dataframe(filtered_datasets_df)

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots()
        sns.countplot(data=filtered_users_df, x="activityStatus", palette="Set2", ax=ax)
        ax.set_title("User Activity Status")
        st.pyplot(fig)

    with col2:
        heatmap_data = filtered_activity_df.groupby(["User email", "Artifact Name"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(6, 3))
        sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.3, ax=ax, cbar=False)
        ax.set_title("Access Heatmap")
        st.pyplot(fig)

    # Trends
    col3, col4 = st.columns(2)
    with col3:
        top_reports = filtered_activity_df["Artifact Name"].value_counts().head(10).reset_index()
        top_reports.columns = ["Report Name", "Access Count"]
        fig, ax = plt.subplots()
        sns.barplot(data=top_reports, x="Access Count", y="Report Name", palette="crest", ax=ax)
        ax.set_title("Top Accessed Reports")
        st.pyplot(fig)

    with col4:
        filtered_activity_df["YearMonth"] = filtered_activity_df["Activity time"].dt.to_period("M").astype(str)
        monthly_usage = filtered_activity_df.groupby("YearMonth").size().reset_index(name="Access Count")
        monthly_usage["YearMonth"] = pd.to_datetime(monthly_usage["YearMonth"])
        fig, ax = plt.subplots()
        sns.barplot(data=monthly_usage, x="YearMonth", y="Access Count", color="skyblue", ax=ax)
        ax.set_title("Monthly Usage Trend")
        ax.set_xticklabels([d.strftime('%b %Y') for d in monthly_usage["YearMonth"]], rotation=45)
        st.pyplot(fig)
