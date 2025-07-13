import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace
apply_sidebar_style()
show_workspace()
def render_top_engagement_insights(activity_df, users_df, reports_df, datasets_df, fig_alpha=0.01):
    st.subheader("🏆 Top Engagement Insights")
    col1, col2, col3, col4 = st.columns(4)

    # Top Reports
    with col1:
        st.subheader("📊 Top 5 Reports")
        top_reports = activity_df[activity_df["ArtifactId"].isin(reports_df["id"])]
        report_usage = top_reports["ArtifactId"].value_counts().head(5).reset_index()
        report_usage.columns = ["Report ID", "Usage Count"]
        report_usage = report_usage.merge(reports_df[["id", "name"]], left_on="Report ID", right_on="id", how="left")
        fig1, ax1 = plt.subplots(figsize=(4, 3))
        fig1.patch.set_alpha(fig_alpha)
        ax1.patch.set_alpha(fig_alpha)
        sns.barplot(data=report_usage, x="Usage Count", y="name", palette="viridis", ax=ax1)
        ax1.set_title("Top Reports", color="gray")
        ax1.tick_params(colors="gray")
        for label in ax1.get_xticklabels() + ax1.get_yticklabels():
            label.set_color("gray")
        st.pyplot(fig1)

    # Top Datasets
    with col2:
        st.subheader("📦 Top 5 Datasets")
        top_datasets = activity_df[activity_df["ArtifactId"].isin(datasets_df["id"])]
        dataset_usage = top_datasets["ArtifactId"].value_counts().head(5).reset_index()
        dataset_usage.columns = ["Dataset ID", "Usage Count"]
        dataset_usage = dataset_usage.merge(datasets_df[["id", "name"]], left_on="Dataset ID", right_on="id", how="left")
        fig2, ax2 = plt.subplots(figsize=(4, 3))
        fig2.patch.set_alpha(fig_alpha)
        ax2.patch.set_alpha(fig_alpha)
        sns.barplot(data=dataset_usage, x="Usage Count", y="name", palette="crest", ax=ax2)
        ax2.set_title("Top Datasets", color="gray")
        ax2.tick_params(colors="gray")
        for label in ax2.get_xticklabels() + ax2.get_yticklabels():
            label.set_color("gray")
        st.pyplot(fig2)

    # Top Users
    with col3:
        st.subheader("👤 Top 5 Users")
        user_activity = activity_df["User email"].value_counts().head(5).reset_index()
        user_activity.columns = ["User Email", "Activity Count"]
        user_activity = user_activity.merge(users_df[["emailAddress", "displayName"]], left_on="User Email", right_on="emailAddress", how="left")
        fig3, ax3 = plt.subplots(figsize=(4, 3))
        fig3.patch.set_alpha(fig_alpha)
        ax3.patch.set_alpha(fig_alpha)
        sns.barplot(data=user_activity, x="Activity Count", y="displayName", palette="Blues_d", ax=ax3)
        ax3.set_title("Top Users", color="gray")
        ax3.tick_params(colors="gray")
        for label in ax3.get_xticklabels() + ax3.get_yticklabels():
            label.set_color("gray")
        st.pyplot(fig3)

    # Top Active Users (Last 3 Months)
    with col4:
        st.subheader("⏱️ Active Users (3 Months)")
        recent_activity_df = activity_df[activity_df["Activity time"] >= pd.Timestamp.now() - pd.DateOffset(months=3)]
        recent_user_activity = recent_activity_df["User email"].value_counts().head(5).reset_index()
        recent_user_activity.columns = ["User Email", "Activity Count"]
        recent_user_activity = recent_user_activity.merge(users_df[["emailAddress", "displayName"]], left_on="User Email", right_on="emailAddress", how="left")
        fig4, ax4 = plt.subplots(figsize=(4, 3))
        fig4.patch.set_alpha(fig_alpha)
        ax4.patch.set_alpha(fig_alpha)
        sns.barplot(data=recent_user_activity, x="Activity Count", y="displayName", palette="PuBuGn", ax=ax4)
        ax4.set_title("Top Active Users", color="gray")
        ax4.tick_params(colors="gray")
        for label in ax4.get_xticklabels() + ax4.get_yticklabels():
            label.set_color("gray")
        st.pyplot(fig4)
