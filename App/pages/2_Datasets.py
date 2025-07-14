'''import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

apply_sidebar_style()
show_workspace()

st.markdown("<h1 style='text-align: center;'>📊 Datasets</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Validate session state
if not (st.session_state.get("access_token") and st.session_state.get("workspace_ids") and st.session_state.get("user_email")):
    st.warning("❌ Missing credentials or workspace selection.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Aggregate data
reports_df_list, datasets_df_list, users_df_list = [], [], []
for ws_id in workspace_ids:
    reports, datasets, users = get_filtered_dataframes(token, ws_id, email)
    workspace_name = workspace_map.get(ws_id, "Unknown")
    reports["workspace_id"] = ws_id
    datasets["workspace_id"] = ws_id
    users["workspace_id"] = ws_id
    reports["workspace_name"] = workspace_name
    datasets["workspace_name"] = workspace_name
    users["workspace_name"] = workspace_name
    reports_df_list.append(reports)
    datasets_df_list.append(datasets)
    users_df_list.append(users)

reports_df = pd.concat(reports_df_list, ignore_index=True)
datasets_df = pd.concat(datasets_df_list, ignore_index=True)
users_df = pd.concat(users_df_list, ignore_index=True)

if datasets_df.empty:
    st.warning("📭 No dataset data available.")
    st.stop()

# Theme-based transparency
fig_alpha = 0.5 if st.get_option("theme.base") == "dark" else 0.01

col1, col2 = st.columns(2)
with col1:
    st.subheader("📓 Dataset Status vs Freshness")
    group = datasets_df.groupby(["datasetStatus", "outdated"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)
    ax.title.set_color("gray")
    ax.tick_params(colors="gray")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color("gray")
    group.plot(kind="bar", stacked=True, ax=ax, colormap="coolwarm")
    st.pyplot(fig)

with col2:
    st.subheader("📅 Dataset Creation Timeline")
    datasets_df["createdDate"] = pd.to_datetime(datasets_df["createdDate"])
    created_by_month = datasets_df["createdDate"].dt.to_period("M").value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)
    ax.set_title("Created Per Month", color="gray")
    created_by_month.plot(kind="line", marker="o", color="steelblue", ax=ax)
    ax.tick_params(colors="gray")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color("gray")
    st.pyplot(fig)

col1, col2 = st.columns(2)
with col1:
    st.subheader("📈 Refreshable vs Non-Refreshable Datasets")
    group = datasets_df["isRefreshable"].value_counts().rename(index={True: "Refreshable", False: "Static"})
    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)
    ax.set_title("Refresh Capability", color="gray")
    group.plot(kind="bar", color=["green", "red"], ax=ax)
    ax.tick_params(colors="gray")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color("gray")
    st.pyplot(fig)

with col2:
    st.subheader("🌡️ Heatmap: Report vs Dataset Status")
    cross = pd.crosstab(reports_df["Reportstatus Based on Dataset"], reports_df["datasetStatus"])
    fig, ax = plt.subplots(figsize=(4, 3))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)
    sns.heatmap(cross, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.tick_params(colors="gray")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color("gray")
    st.pyplot(fig)

# View or Explore Buttons
if "veiw_datasets" not in st.session_state:
    st.session_state.veiw_datasets = False
if "Explore_datasets_dataframe" not in st.session_state:
    st.session_state.Explore_datasets_dataframe = False

with st.container():
    col1, col2, col3, col4, col5 = st.columns([1,3,3,4,1])
    with col2:
        if st.button("📄 View Datasets"):
            st.session_state.veiw_datasets = True
            st.session_state.Explore_datasets_dataframe = False
    with col4:
        if st.button("📄 Explore Datasets DataFrame"):
            st.session_state.veiw_datasets = False
            st.session_state.Explore_datasets_dataframe = True

if st.session_state.veiw_datasets:
    st.markdown(" 🔗 Datasets Overview")
    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns([3, 3, 2, 2, 2, 2])
        col1.markdown("🔖 ID")
        col2.markdown("📛 Name")
        col3.markdown("👤 By")
        col4.markdown("📅 Created")
        col5.markdown("🏢 Workspace")
        col6.markdown("🔍 Link")

    for index, row in datasets_df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([3, 3, 2, 2, 2, 2])
            col1.markdown(f"**{row['id']}**")
            col2.markdown(f"**{row['name']}**")
            col3.markdown(f"`{row['configuredBy']}`")
            col4.write(f"**{row['createdDate']}**")
            col5.markdown(f"`{row['workspace_name']}`")
            col6.markdown(
                f"""<a href="{row['webUrl']}" target="_blank"><button style='font-size: 0.8rem;'>🚀 Explore</button></a>""",
                unsafe_allow_html=True
            )

elif st.session_state.Explore_datasets_dataframe:
    st.dataframe(datasets_df)
'''

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
st.markdown("<h2 style='text-align: center;'>📦 Datasets</h2><hr>", unsafe_allow_html=True)

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

# Filtered View
if st.session_state.dataset_filter_status:
    st.markdown(f"## 📦 Filtered Datasets: `{st.session_state.dataset_filter_status}`")
    if st.session_state.dataset_filter_status == "Outdated":
        filtered_df = datasets_df[datasets_df["outdated"] == True]
    else:
        filtered_df = datasets_df[datasets_df["datasetStatus"] == st.session_state.dataset_filter_status]

    ws_counts = filtered_df["workspace_name"].value_counts().reset_index()
    ws_counts.columns = ["Workspace", "Count"]
    st.markdown("### 🧮 Count by Workspace")
    st.dataframe(ws_counts, use_container_width=True)

    for ws_name, group in filtered_df.groupby("workspace_name"):
        st.markdown(f"### 🏢 Workspace: `{ws_name}` ({len(group)} datasets)")

        header1, header2, header3, header4, header5, header6, header7, header8 = st.columns([3, 3, 2, 2, 2, 2, 2, 2])
        header1.markdown("ID")
        header2.markdown("Name")
        header3.markdown("By")
        header4.markdown("CreatedDate")
        header5.markdown("🧮 Status")
        header6.markdown("⚙️ Refreshable")
        header7.markdown("🔍 Link")

        for _, row in group.iterrows():
            with st.container():
                col1, col2, col3, col4, col5, col6, col7= st.columns([3, 3, 2, 2, 2, 2, 2 ])
                col1.markdown(f"`{row['id']}`")
                col2.markdown(f"**{row['name']}**")
                col3.markdown(row["configuredBy"])
                col4.markdown(row["createdDate"])
                col5.markdown(row["datasetStatus"])
                col6.markdown("✅ Yes" if row["isRefreshable"] else "No")
                col7.markdown(f"""<a href="{row['webUrl']}" target="_blank">
                    <button style='font-size: 0.8rem;'>🚀 Explore</button></a>""", unsafe_allow_html=True)

# View Datasets (Grouped)
elif st.session_state.view_datasets:
    st.markdown("## 🗂️ Datasets Overview by Workspace")

    for ws_name, group in datasets_df.groupby("workspace_name"):
        st.markdown(f"### 🏢 Workspace: `{ws_name}` ({len(group)} datasets)")

        # Header row
        header1, header2, header3, header4, header5, header6, header7, header8 = st.columns([2.5, 3, 2, 2.5, 2.5, 1.5, 1.5, 2])
        header1.markdown(" **ID**")
        header2.markdown(" **Name**")
        header3.markdown(" **Configured By**")
        header4.markdown("**Created Date**")
        header5.markdown("**Status**")
        header6.markdown("**Refreshable**")
        header7.markdown("**Outdated**")
        header8.markdown(" **Actions**")

        for _, row in group.iterrows():
            with st.container():
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2.5, 3, 2, 2.5, 2.5, 1.5, 1.5, 2])
                col1.markdown(f"`{row['id']}`")
                col2.markdown(f"**{row['name']}**")

                # Email with mailto link
                configured_by = row.get("configuredBy", "")
                if "@" in configured_by:
                    email_link = f"[{configured_by}](mailto:{configured_by})"
                    col3.markdown(email_link)
                else:
                    col3.markdown(configured_by)

                col4.markdown(str(row["createdDate"]))
                col5.markdown(row["datasetStatus"])
                col6.markdown("✅" if row["isRefreshable"] else "❌")
                col7.markdown("✅" if row["outdated"] else "❌")
                col8.markdown(f"""<a href="{row['webUrl']}" target="_blank">
                    <button style='font-size:0.75rem;'>🚀 Explore</button></a>""", unsafe_allow_html=True)

# Explore DataFrame View
elif st.session_state.explore_datasets_dataframe:
    st.markdown("## 📊 Full Datasets Table by Workspace")
    for ws_name, group in datasets_df.groupby("workspace_name"):
        st.markdown(f"### 🏢 Workspace: `{ws_name}`")

        renamed_df = group.rename(columns={
            "id": "ID",
            "name": "Name",
            "configuredBy": "By",
            "createdDate": "Created",
            "datasetStatus": "Status",
            "outdated": "Outdated",
            "isRefreshable": "Refreshable",
            "webUrl": "Link"
        })[["ID", "Name", "By", "Created", "Status", "Outdated", "Refreshable", "Link"]]

        st.dataframe(renamed_df, use_container_width=True)
