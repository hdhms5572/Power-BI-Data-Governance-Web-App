import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import plotly.express as px
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

from utils import  render_profile_header
def inject_external_style():
    with open("static/style.css") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Initial UI setup
apply_sidebar_style()
render_profile_header()
show_workspace()
inject_external_style()

col1, col2, col3 = st.columns(3)
with col2:
    st.image("./images/dover_log.png")
st.markdown("<h1 style='text-align: center;'>📊Reports</h1>", unsafe_allow_html=True)

# Professional Dashboard Description
st.markdown("""
<div style='text-align: center; font-size: 1.05rem; background-color: #E7DBF3; padding: 14px 24px; border-left: 6px solid #673ab7; border-radius: 8px; margin-bottom: 25px;'>
This dashboard provides a comprehensive view of Power BI reports across  selected workspaces. 
Analyze report statuses, explore associated datasets, and generate insights through intuitive charts and tables.
</div><hr>
""", unsafe_allow_html=True)

# Session Validation
if not (st.session_state.get("access_token") and
        st.session_state.get("workspace_ids") and
        st.session_state.get("user_email")):
    st.warning("Missing credentials or workspace selection.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Data Loading
reports_df_list, datasets_df_list, users_df_list = [], [], []
for ws_id in workspace_ids:
    reports, datasets, users = get_filtered_dataframes(token, ws_id, email)
    reports["workspace_id"] = ws_id
    reports["workspace_name"] = workspace_map.get(ws_id, "Unknown")
    reports_df_list.append(reports)
    datasets_df_list.append(datasets)
    users_df_list.append(users)

reports_df = pd.concat(reports_df_list, ignore_index=True)
datasets_df = pd.concat(datasets_df_list, ignore_index=True)

if reports_df.empty:
    st.warning("No reports found across selected workspaces.")
    st.stop()

# State Setup
st.session_state.setdefault("filter_status", None)
st.session_state.setdefault("view_reports", False)
st.session_state.setdefault("explore_reports_dataframe", False)
st.session_state.setdefault("selected_dataset_id", None)

# grid Filters 
status_series = reports_df["Reportstatus Based on Dataset"]
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🧮 Total Reports"):
        st.session_state.filter_status = None
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Total Reports</div><div class='grid-value'>{len(reports_df)}</div></div>", unsafe_allow_html=True)
with col2:
    if st.button("✅ Active"):
        st.session_state.filter_status = "Active"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Active</div><div class='grid-value'>{(status_series == 'Active').sum()}</div></div>", unsafe_allow_html=True)
with col3:
    if st.button("⏳ Outdated"):
        st.session_state.filter_status = "Active (Outdated)"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Active (Outdated)</div><div class='grid-value'>{(status_series == 'Active (Outdated)').sum()}</div></div>", unsafe_allow_html=True)
with col4:
    if st.button("🚫 Inactive"):
        st.session_state.filter_status = "Inactive"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Inactive</div><div class='grid-value'>{(status_series == 'Inactive').sum()}</div></div>", unsafe_allow_html=True)

st.markdown("---")

# Visualizations

col1, col2 = st.columns(2)
with col1:
    st.subheader("Report Status Distribution by Workspace")
    workspace_names = reports_df["workspace_name"].unique()
    workspace_palette = dict(zip(
        workspace_names,
        matplotlib.colormaps["tab10"].colors[:len(workspace_names)]
    ))
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.countplot(
        data=reports_df,
        x="Reportstatus Based on Dataset",
        hue="workspace_name",
        palette=workspace_palette,
        ax=ax
    )
    st.pyplot(fig)

with col2:
    st.subheader("Overall Report Status Share")
    status_counts = reports_df["Reportstatus Based on Dataset"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 3))

    wedges, texts, autotexts = ax.pie(
        status_counts,
        labels=status_counts.index,
        autopct="%1.1f%%",
        colors=["green", "red", "orange"],
        startangle=150
    )
    for text in texts:
        text.set_fontweight("bold")
    ax.axis("equal")
    st.pyplot(fig)

# Top Datasets by Report Count
st.header('Top Datasets by Report Count')
dataset_counts = reports_df['datasetId'].value_counts().reset_index()
dataset_counts.columns = ['datasetId', 'report_count']

# Step 2: Merge with dataset names
top_datasets = pd.merge(
    dataset_counts.head(10),
    datasets_df[['id', 'name']],
    left_on='datasetId',
    right_on='id',
    how='left'
)
top_datasets.rename(columns={'name': 'Dataset Name'}, inplace=True)
top_datasets = top_datasets.sort_values(by='report_count', ascending=True)

fig = px.treemap(
    top_datasets,
    path=['Dataset Name'],
    values='report_count',
    color='report_count',
    color_continuous_scale='Blues'
)
st.plotly_chart(fig, use_container_width=True)

# View Toggles 
colA, colB = st.columns([1, 1])
with colA:
    if st.button("📋 View Reports"):
        st.session_state.view_reports = True
        st.session_state.explore_reports_dataframe = False
        st.session_state.filter_status = None
with colB:
    if st.button("📊 Explore Reports DataFrame"):
        st.session_state.view_reports = False
        st.session_state.explore_reports_dataframe = True
        st.session_state.filter_status = None


if st.session_state.filter_status:
    st.markdown(f"## 🧾 Filtered Reports: `{st.session_state.filter_status}`")

    filtered_df = reports_df[reports_df["Reportstatus Based on Dataset"] == st.session_state.filter_status]

    # Summary table: count per workspace
    workspace_counts = filtered_df["workspace_name"].value_counts().reset_index()
    workspace_counts.columns = ["Workspace", "Count"]
    st.markdown("### 🗂️ Status Count by Workspace")
    st.dataframe(workspace_counts, use_container_width=True)


    # Header row
    st.markdown('<div class="classic-table">', unsafe_allow_html=True)
    st.markdown('<div class="classic-row header">', unsafe_allow_html=True)
    header1, header2, header3, header4, header5 = st.columns([4, 2, 3, 3, 2])
    header1.markdown("**Report Name**")
    header2.markdown("**Status**")
    header3.markdown("**Workspace**")
    header4.markdown("**Dataset**")
    header5.markdown("**Link**")
    st.markdown('</div>', unsafe_allow_html=True)

    # Report rows
    for _, row in filtered_df.iterrows():
        st.markdown('<div class="classic-row">', unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns([4, 2, 3, 3, 2])
        col1.markdown(row['name'])
        col2.markdown(row['Reportstatus Based on Dataset'])
        col3.markdown(row['workspace_name'])

        dataset_name = datasets_df.loc[datasets_df['id'] == row['datasetId'], 'name'].values
        dataset_label = dataset_name[0] if len(dataset_name) > 0 else "No Dataset"
        if col4.button(dataset_label, key=f"btn_{row['id']}"):
            st.session_state.selected_dataset_id = row['datasetId']

        col5.markdown(f"""<a href="{row['webUrl']}" target="_blank">
                        <button style='font-size: 0.8rem;'>🚀 Explore</button></a>""",
                    unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.selected_dataset_id == row['datasetId']:
            selected_dataset = datasets_df[datasets_df["id"] == row["datasetId"]]
            if not selected_dataset.empty:
                st.markdown(f"### 📦 Dataset Info for `{row['datasetId']}`")
                st.dataframe(selected_dataset, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)



elif st.session_state.view_reports:
    st.markdown("## 🗂️ Reports Grouped by Workspace")
    for ws_name, group in reports_df.groupby("workspace_name"):
        st.markdown(f"### 📍 Workspace: `{ws_name}` ({len(group)} reports)")

        st.markdown('<div class="classic-table">', unsafe_allow_html=True)
        st.markdown('<div class="classic-row header">', unsafe_allow_html=True)
        header1, header2, header3, header4 = st.columns([4, 3, 3, 2])
        header1.markdown("**Report Name**")
        header2.markdown("**Status**")  
        header3.markdown("**Dataset**")
        header4.markdown("**Link**")

        for _, row in group.iterrows():
            st.markdown('<div class="classic-row">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([4, 3, 3, 2])

            col1.markdown(f"**{row['name']}**")
            col2.markdown(row['Reportstatus Based on Dataset'])

            dataset_name = datasets_df.loc[datasets_df['id'] == row['datasetId'], 'name'].values
            dataset_label = dataset_name[0] if len(dataset_name) > 0 else "No Dataset"
            if col3.button(dataset_label, key=f"btn_ws_{row['id']}"):
                st.session_state.selected_dataset_id = row['datasetId']

            col4.markdown(f"""<a href="{row['webUrl']}" target="_blank">
                <button style='font-size: 0.8rem;'>🚀 Explore</button></a>""",
                unsafe_allow_html=True)

            if st.session_state.selected_dataset_id == row['datasetId']:
                selected_dataset = datasets_df[datasets_df["id"] == row["datasetId"]]
                if not selected_dataset.empty:
                    st.markdown(f"Dataset Info for `{row['datasetId']}`")
                    st.dataframe(selected_dataset, use_container_width=True)

# Explore Reports Table View
elif st.session_state.explore_reports_dataframe:
    st.markdown("## 📊 Full Reports Table Grouped by Workspace")
    for ws_name, group in reports_df.groupby("workspace_name"):

        renamed_df = group.rename(columns={
            "name": "Report Name",
            "webUrl": "Report URL",
            "Reportstatus Based on Dataset": "Status"
        })[["Report Name", "Report URL", "Status"]].reset_index(drop=True)

        col1, col2 = st.columns([5,1])
        with col1:
            st.markdown(f"Workspace: `{ws_name}` ({len(group)} reports)")
        with col2:
            csv = renamed_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{ws_name}_activity_log.csv",
                mime="text/csv"
            )

        st.dataframe(renamed_df, use_container_width=True)



        
