import streamlit as st
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
