import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace
def inject_external_style():
    with open("static/style.css") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Initial UI setup
apply_sidebar_style()
show_workspace()
inject_external_style()
st.markdown("<h2 style='text-align: center;'>DATASETS</h2><hr>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; font-size: 1.05rem; color: #333; background-color: #f5f9ff;
     padding: 12px 24px; border-left: 5px solid #1a73e8; border-radius: 6px; margin-bottom: 20px;'>
📂 This dashboard provides an in-depth overview of Power BI datasets available in your selected workspaces. 
Track dataset freshness, refreshability, creation trends, and dataset-to-report relationships using visual summaries and interactive tables.
</div>
""", unsafe_allow_html=True)
# Validate session
if not (st.session_state.get("access_token") and st.session_state.get("workspace_ids") and st.session_state.get("user_email")):
    st.warning("❌ Missing credentials or workspace selection.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Load data
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
    st.warning("📭 No dataset data available.")
    st.stop()

# State setup
st.session_state.setdefault("dataset_filter_status", None)
st.session_state.setdefault("view_datasets", False)
st.session_state.setdefault("explore_datasets_dataframe", False)

# KPI Filters
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🧮 Total Datasets"):
        st.session_state.dataset_filter_status = None
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Total</div><div class='grid-value'>{len(datasets_df)}</div></div>", unsafe_allow_html=True)

with col2:
    if st.button("✅ Active"):
        st.session_state.dataset_filter_status = "Active"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Active</div><div class='grid-value'>{(datasets_df['datasetStatus'] == 'Active').sum()}</div></div>", unsafe_allow_html=True)

with col3:
    if st.button("⏳ Outdated"):
        st.session_state.dataset_filter_status = "Outdated"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Outdated</div><div class='grid-value'>{(datasets_df['outdated'] == True).sum()}</div></div>", unsafe_allow_html=True)

with col4:
    if st.button("🚫 Inactive"):
        st.session_state.dataset_filter_status = "Inactive"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Inactive</div><div class='grid-value'>{(datasets_df['datasetStatus'] == 'Inactive').sum()}</div></div>", unsafe_allow_html=True)

st.markdown("---")

# Visualizations
col1, col2 = st.columns(2)
with col1:
    st.subheader("📓 Dataset Status vs Freshness")
    freshness_group = datasets_df.groupby(["datasetStatus", "outdated"]).size().unstack(fill_value=0)
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
    cross_tab = pd.crosstab(reports_df["Reportstatus Based on Dataset"], reports_df["datasetStatus"])
    fig4, ax4 = plt.subplots(figsize=(4, 3))
    sns.heatmap(cross_tab, annot=True, fmt="d", cmap="Blues", ax=ax4)
    st.pyplot(fig4)

st.markdown("---")

# View toggles
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

# Columns to display
display_cols = ["name", "configuredBy", "isRefreshable", "createdDate", "outdated", "datasetStatus"]

# Filtered View
if st.session_state.dataset_filter_status:
    st.markdown(f"## 📦 Filtered Datasets: `{st.session_state.dataset_filter_status}`")
    
    # Apply dataset status filter
    if st.session_state.dataset_filter_status == "Outdated":
        filtered_df = datasets_df[datasets_df["outdated"] == True]
    else:
        filtered_df = datasets_df[datasets_df["datasetStatus"] == st.session_state.dataset_filter_status]

    # Count by workspace
    ws_counts = filtered_df["workspace_name"].value_counts().reset_index()
    ws_counts.columns = ["Workspace", "Count"]
    st.markdown("### 🧮 Count by Workspace")
    st.dataframe(ws_counts, use_container_width=True)

    # Display filtered datasets per workspace
    for ws_name, group in filtered_df.groupby("workspace_name"):
        st.markdown(f"### 🏢 Workspace: `{ws_name}` ({len(group)} datasets)")
        group = group[display_cols + ["webUrl"]]  # Keep webUrl for Explore button

        # Header row (ID removed)
        header1, header2, header3, header4, header5, header6 = st.columns([3, 3, 2, 2, 2, 2])
        header1.markdown("**Name**")
        header2.markdown("**By**")
        header3.markdown("**Created Date**")
        header4.markdown("** Status**")
        header5.markdown("** Refreshable**")
        header6.markdown("**🔍 Link**")

        for _, row in group.iterrows():
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 3, 2, 2, 2, 2])
                col1.markdown(f"**{row['name']}**")
                col2.markdown(row["configuredBy"])
                col3.markdown(str(row["createdDate"]))
                col4.markdown(row["datasetStatus"])
                col5.markdown("✅ Yes" if row["isRefreshable"] else "❌ No")
                col6.markdown(f"""<a href="{row['webUrl']}" target="_blank">
                    <button style='font-size: 0.8rem;'>🚀 Explore</button></a>""", unsafe_allow_html=True)

# View Datasets (Grouped)
elif st.session_state.view_datasets:
    st.markdown("## 🗂️ Datasets Overview by Workspace")

    for ws_name, group in datasets_df.groupby("workspace_name"):
        group = group[display_cols + ["webUrl"]]  # Removed "id"

        st.markdown(f"### 🏢 Workspace: `{ws_name}` ({len(group)} datasets)")

        header1, header2, header3, header4, header5, header6 = st.columns([3, 3, 2.5, 2.5, 1.5, 2])
        header1.markdown("**Name**")
        header2.markdown("**Configured By**")
        header3.markdown("**Created Date**")
        header4.markdown("**Status**")
        header5.markdown("**Refreshable**")
        header6.markdown("**Actions**")

        for _, row in group.iterrows():
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 3, 2.5, 2.5, 1.5, 2])
                col1.markdown(f"**{row['name']}**")

                configured_by = row.get("configuredBy", "")
                if "@" in configured_by:
                    email_link = f"[{configured_by}](mailto:{configured_by})"
                    col2.markdown(email_link)
                else:
                    col2.markdown(configured_by)

                col3.markdown(str(row["createdDate"]))
                col4.markdown(row["datasetStatus"])
                col5.markdown("✅" if row["isRefreshable"] else "❌")
                col6.markdown(f"""<a href="{row['webUrl']}" target="_blank">
                    <button style='font-size:0.75rem;'>🚀 Explore</button></a>""", unsafe_allow_html=True)


# Explore DataFrame View
elif st.session_state.explore_datasets_dataframe:
    st.markdown("## 📊 Full Datasets Table by Workspace")

    for ws_name, group in datasets_df.groupby("workspace_name"):
        renamed_df = ( group[display_cols].rename(columns={
        "name": "Name",
        "configuredBy": "Configured By",
        "isRefreshable": "Refreshable",
        "createdDate": "Created Date",
        "outdated": "Outdated",
        "datasetStatus": "Status"
    })[["Name", "Configured By", "Refreshable", "Created Date", "Outdated", "Status"]]
    .reset_index(drop=True))

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"### 🏢 Workspace: `{ws_name}`")
        with col2:
            csv = renamed_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{ws_name}_datasets.csv",
                mime="text/csv"
            )

        st.dataframe(renamed_df, use_container_width=True)
