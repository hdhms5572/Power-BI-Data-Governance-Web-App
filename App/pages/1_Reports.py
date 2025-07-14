import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
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

st.markdown("<h2 style='text-align: center;'>📊 Reports</h2><hr>", unsafe_allow_html=True)

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
# Theme Styling
theme_base = st.get_option("theme.base")
fig_alpha = 1.0 if theme_base == "dark" else 0.01

def style_plot(ax):
    ax.patch.set_alpha(fig_alpha)
    ax.title.set_color("gray")
    ax.xaxis.label.set_color("gray")
    ax.yaxis.label.set_color("gray")
    ax.tick_params(colors="gray")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color("gray")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Report Status Distribution by Workspace")
    workspace_names = reports_df["workspace_name"].unique()
    workspace_palette = dict(zip(
        workspace_names,
        matplotlib.colormaps["tab10"].colors[:len(workspace_names)]
    ))

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_alpha(fig_alpha)
    style_plot(ax)

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
    fig.patch.set_alpha(fig_alpha)
    style_plot(ax)

    wedges, texts, autotexts = ax.pie(
        status_counts,
        labels=status_counts.index,
        autopct="%1.1f%%",
        colors=["green", "red", "orange"],
        startangle=150
    )
    for text in texts:
        text.set_color("gray")
        text.set_fontweight("bold")
    ax.axis("equal")
    st.pyplot(fig)

# Top Datasets by Report Count
st.subheader("Top Datasets by Report Count")
dataset_counts = reports_df['datasetId'].value_counts().reset_index()
dataset_counts.columns = ['datasetId', 'report_count']
top_datasets = pd.merge(
    dataset_counts.head(10),
    datasets_df[['id', 'name']],
    left_on='datasetId',
    right_on='id',
    how='left'
)
top_datasets.rename(columns={'name': 'datasetName'}, inplace=True)
fig, ax = plt.subplots(figsize=(7, 3))
fig.patch.set_alpha(fig_alpha)
style_plot(ax)
sns.barplot(data=top_datasets, x='report_count', y='datasetName', palette='mako', ax=ax)
ax.set_title("Top Datasets", color="gray")
ax.set_xlabel("Report Count", color="gray")
ax.set_ylabel("Dataset Name", color="gray")
st.pyplot(fig)

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

    # Header row for report details
    header1, header2, header3, header4, header5, header6 = st.columns([4, 3, 2, 2, 3, 2])
    header1.markdown("**Report ID**")
    header2.markdown("**Report Name**")
    header3.markdown("**Status**")
    header4.markdown("**Workspace**")
    header5.markdown("**Dataset**")
    header6.markdown("**Link**")

    # Report detail rows
    for _, row in filtered_df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([4, 3, 2, 2, 3, 2])
            col1.markdown(f"`{row['id']}`")
            col2.markdown(f"**{row['name']}**")
            col3.markdown(row['Reportstatus Based on Dataset'])
            col4.markdown(row['workspace_name'])

            # Dataset label button
            dataset_name = datasets_df.loc[datasets_df['id'] == row['datasetId'], 'name'].values
            dataset_label = dataset_name[0] if len(dataset_name) > 0 else "No Dataset"
            if col5.button(dataset_label, key=f"btn_{row['id']}"):
                st.session_state.selected_dataset_id = row['datasetId']

            # Report link
            col6.markdown(f"""<a href="{row['webUrl']}" target="_blank">
                              <button style='font-size: 0.8rem;'>Explore</button></a>""",
                          unsafe_allow_html=True)

            # Display dataset info if selected
            if st.session_state.selected_dataset_id == row['datasetId']:
                selected_dataset = datasets_df[datasets_df["id"] == row["datasetId"]]
                if not selected_dataset.empty:
                    st.markdown(f"### 📦 Dataset Info for `{row['datasetId']}`")
                    st.dataframe(selected_dataset, use_container_width=True)


elif st.session_state.view_reports:
    st.markdown("## 🗂️ Reports Grouped by Workspace")
    for ws_name, group in reports_df.groupby("workspace_name"):
        st.markdown(f"### 📍 Workspace: `{ws_name}` ({len(group)} reports)")

        header1, header2, header3, header4, header5 = st.columns([4, 3, 3, 4, 2])
        header1.markdown("**Report ID**")
        header2.markdown("**Report Name**")
        header3.markdown("**Status**")
        header4.markdown("**Dataset**")
        header5.markdown("**Link**")

        for _, row in group.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([4, 3, 3, 4, 2])
                col1.markdown(f"`{row['id']}`")
                col2.markdown(f"**{row['name']}**")
                col3.markdown(row['Reportstatus Based on Dataset'])

                dataset_name = datasets_df.loc[datasets_df['id'] == row['datasetId'], 'name'].values
                dataset_label = dataset_name[0] if len(dataset_name) > 0 else "No Dataset"
                if col4.button(dataset_label, key=f"btn_ws_{row['id']}"):
                    st.session_state.selected_dataset_id = row['datasetId']

                col5.markdown(f"""<a href="{row['webUrl']}" target="_blank">
                    <button style='font-size: 0.8rem;'>Explore</button></a>""",
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
            "id": "Report ID",
            "name": "Report Name",
            "datasetId": "Dataset ID",
            "webUrl": "Report URL",
            "Reportstatus Based on Dataset": "Status"
        })[["Report ID", "Report Name", "Dataset ID", "Report URL", "Status"]]

        col1, col2 = st.columns([5,1])
        with col1:
            st.markdown(f"### 📍 Workspace: `{ws_name}` ({len(group)} reports)")
        with col2:
            csv = renamed_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{ws_name}_activity_log.csv",
                mime="text/csv"
            )

        st.dataframe(renamed_df, use_container_width=True)

        for _, row in group.iterrows():
            if st.session_state.selected_dataset_id == row["datasetId"]:
                selected_dataset = datasets_df[datasets_df["id"] == row["datasetId"]]
                if not selected_dataset.empty:
                    st.markdown(f"Dataset Info for `{row['datasetId']}`")
                    st.dataframe(selected_dataset, use_container_width=True)

        
