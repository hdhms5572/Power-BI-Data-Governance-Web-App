import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace, render_profile_header

def inject_external_style():
    with open("static/style.css") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

apply_sidebar_style()
render_profile_header()
show_workspace()
inject_external_style()

col1, col2, col3 = st.columns(3)
with col2:
    st.image("./images/dover_log.png")

st.markdown("<h1 style='text-align: center;'>📊 Datasets</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; font-size: 1.05rem; background-color: #E7DBF3; padding: 14px 24px; border-left: 6px solid #673ab7; border-radius: 8px; margin-bottom: 25px;'>
This dashboard provides an in-depth overview of Power BI datasets available in selected workspaces. 
Track dataset freshness, refreshability, creation trends, and dataset-to-report relationships using visual summaries and interactive tables.
</div><hr>
""", unsafe_allow_html=True)

if not (st.session_state.get("access_token") and st.session_state.get("workspace_ids") and st.session_state.get("user_email")):
    st.warning("❌ Missing credentials or workspace selection.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

reports_df_list, datasets_df_list, users_df_list = [], [], []
for ws_id in workspace_ids:
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

if datasets_df.empty:
    st.warning("📍 No dataset data available.")
    st.stop()

st.session_state.setdefault("dataset_filter_status", None)
st.session_state.setdefault("view_datasets", False)
st.session_state.setdefault("explore_datasets_dataframe", False)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🧹 Up to Date"):
        st.session_state.dataset_filter_status = "Up to Date"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Up to Date</div><div class='grid-value'>{(datasets_df['Dataset Freshness Status'] == 'Up to Date').sum()}</div></div>", unsafe_allow_html=True)

with col2:
    if st.button("⚠️ Needs Attention"):
        st.session_state.dataset_filter_status = "Needs Attention"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Needs Attention</div><div class='grid-value'>{(datasets_df['Dataset Freshness Status'] == 'Needs Attention').sum()}</div></div>", unsafe_allow_html=True)

with col3:
    if st.button("🚫 Expired"):
        st.session_state.dataset_filter_status = "Expired"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Expired</div><div class='grid-value'>{(datasets_df['Dataset Freshness Status'] == 'Expired').sum()}</div></div>", unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📓 Dataset Freshness Breakdown")
    freshness_group = datasets_df.groupby(["Dataset Freshness Status", "isRefreshable"]).size().unstack(fill_value=0)
    fig1, ax1 = plt.subplots(figsize=(6, 3))
    freshness_group.plot(kind="bar", stacked=True, ax=ax1, colormap="coolwarm")
    st.pyplot(fig1)

with col2:
    st.subheader("📅 Dataset Creation Timeline")
    datasets_df["createdDate"] = pd.to_datetime(datasets_df["createdDate"], errors="coerce")
    created_by_month = datasets_df["createdDate"].dt.to_period("M").value_counts().sort_index()
    fig2, ax2 = plt.subplots(figsize=(6, 3))
    created_by_month.plot(kind="line", marker="o", color="steelblue", ax=ax2)
    st.pyplot(fig2)

col3, col4 = st.columns(2)
with col3:
    st.subheader("📈 Refreshable vs Static Datasets")
    refresh_group = datasets_df["isRefreshable"].value_counts().rename({True: "Refreshable", False: "Static"})
    fig3, ax3 = plt.subplots(figsize=(6, 3))
    sns.barplot(x=refresh_group.index, y=refresh_group.values, palette=["#4CAF50", "#F44336"], ax=ax3)
    ax3.set_ylabel("Count")
    st.pyplot(fig3)

with col4:
    st.subheader("🌡️ Heatmap: Report vs Dataset Status")
    cross_tab = pd.crosstab(reports_df["Reportstatus Based on Dataset"], reports_df["Dataset Freshness Status"])
    fig4, ax4 = plt.subplots(figsize=(4, 3))
    sns.heatmap(cross_tab, annot=True, fmt="d", cmap="Blues", ax=ax4)
    st.pyplot(fig4)

st.markdown("---")

colA, colB = st.columns([1, 1])
with colA:
    if st.button("📋 View Datasets"):
        st.session_state.view_datasets = True
        st.session_state.explore_datasets_dataframe = False
        st.session_state.dataset_filter_status = None

with colB:
    if st.button("📊 Explore Datasets DataFrame"):
        st.session_state.view_datasets = False
        st.session_state.explore_datasets_dataframe = True
        st.session_state.dataset_filter_status = None

view_cols = ["name", "configuredBy", "isRefreshable", "createdDate", "outdated", "Dataset Freshness Status"]

if st.session_state.dataset_filter_status:
    st.markdown(f"## 📦 Filtered Datasets: `{st.session_state.dataset_filter_status}`")
    filtered_df = datasets_df[datasets_df["Dataset Freshness Status"] == st.session_state.dataset_filter_status]

    ws_counts = filtered_df["workspace_name"].value_counts().reset_index()
    ws_counts.columns = ["Workspace", "Count"]
    st.markdown("### 🧹 Count by Workspace")
    st.dataframe(ws_counts, use_container_width=True)

    for ws_name, group in filtered_df.groupby("workspace_name"):
        st.markdown(f"### 🏢 Workspace: `{ws_name}` ({len(group)} datasets)")
        st.dataframe(group[view_cols + ["webUrl"]], use_container_width=True)

elif st.session_state.view_datasets:
    st.markdown("## 📂 Datasets Overview by Workspace")
    for ws_name, group in datasets_df.groupby("workspace_name"):
        st.markdown(f"### 🏢 Workspace: `{ws_name}` ({len(group)} datasets)")
        st.dataframe(group[view_cols + ["webUrl"]], use_container_width=True)

elif st.session_state.explore_datasets_dataframe:
    st.markdown("## 📊 Full Datasets Table by Workspace")
    for ws_name, group in datasets_df.groupby("workspace_name"):
        renamed_df = (group[view_cols].rename(columns={
            "name": "Name",
            "configuredBy": "Configured By",
            "isRefreshable": "Refreshable",
            "createdDate": "Created Date",
            "outdated": "Outdated",
            "Dataset Freshness Status": "Status"
        }).reset_index(drop=True))

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"### 🏢 Workspace: `{ws_name}`")
        with col2:
            csv = renamed_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📅 Download CSV",
                data=csv,
                file_name=f"{ws_name}_datasets.csv",
                mime="text/csv"
            )
        st.dataframe(renamed_df, use_container_width=True)
