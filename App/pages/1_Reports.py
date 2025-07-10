import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

apply_sidebar_style()
show_workspace()

st.markdown("<h1 style='text-align: center;'>Reports</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Validate Session State
if not (st.session_state.get("access_token") and st.session_state.get("workspace_ids") and st.session_state.get("user_email")):
    st.warning("Missing credentials or workspace selection.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Collect Data
reports_df_list = []
datasets_df_list = []
users_df_list = []

for ws_id in workspace_ids:
    reports, datasets, users = get_filtered_dataframes(token, ws_id, email)
    reports["workspace_id"] = ws_id
    reports["workspace_name"] = workspace_map.get(ws_id, "Unknown")
    reports_df_list.append(reports)
    datasets_df_list.append(datasets)
    users_df_list.append(users)

reports_df = pd.concat(reports_df_list, ignore_index=True)
datasets_df = pd.concat(datasets_df_list, ignore_index=True)
users_df = pd.concat(users_df_list, ignore_index=True)

if reports_df.empty:
    st.warning("No reports found across selected workspaces.")
    st.stop()

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
top_datasets = dataset_counts.head(10)

fig, ax = plt.subplots(figsize=(7, 3))
fig.patch.set_alpha(fig_alpha)
style_plot(ax)
sns.barplot(data=top_datasets, x='report_count', y='datasetId', palette='mako', ax=ax)
ax.set_title("Top Datasets", color="gray")
ax.set_xlabel("Report Count", color="gray")
ax.set_ylabel("Dataset ID", color="gray")
st.pyplot(fig)

# Toggle Options
if "view_reports" not in st.session_state:
    st.session_state.view_reports = False
if "explore_reports_dataframe" not in st.session_state:
    st.session_state.explore_reports_dataframe = False

with st.container():
    col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 4, 1])
    with col2:
        if st.button("View Reports"):
            st.session_state.view_reports = True
            st.session_state.explore_reports_dataframe = False
    with col4:
        if st.button("Explore Reports DataFrame"):
            st.session_state.view_reports = False
            st.session_state.explore_reports_dataframe = True

# Detailed Report Table
if st.session_state.view_reports:
    if "selected_dataset_id" not in st.session_state:
        st.session_state.selected_dataset_id = None

    st.markdown("Reports Overview")
    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns([4, 3, 2, 2, 3, 2])
        col1.markdown("ID")
        col2.markdown("Name")
        col3.markdown("Status")
        col4.markdown("Workspace")
        col5.markdown("Dataset")
        col6.markdown("Link")

    for index, row in reports_df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([4, 3, 2, 2, 3, 2])
            col1.markdown(f"`{row['id']}`")
            col2.markdown(f"**{row['name']}**")
            col3.markdown(f"{row.get('Reportstatus Based on Dataset', 'Unknown')}")
            col4.markdown(f"{row['workspace_name']}")

            dataset_name = datasets_df.loc[datasets_df['id'] == row['datasetId'], 'name'].values
            dataset_label = dataset_name[0] if len(dataset_name) > 0 else "Unnamed Dataset"
            if col5.button(dataset_label, key=f"btn_{row['id']}"):
                st.session_state.selected_dataset_id = (
                    row['datasetId'] if st.session_state.selected_dataset_id != row['datasetId'] else None
                )
            col6.markdown(
                f"""<a href="{row['webUrl']}" target="_blank"><button style='font-size: 0.8rem;'>Explore</button></a>""",
                unsafe_allow_html=True
            )

            if st.session_state.selected_dataset_id == row['datasetId']:
                selected_dataset = datasets_df[datasets_df["id"] == row["datasetId"]]
                if not selected_dataset.empty:
                    st.markdown(f"Dataset Info for `{row['datasetId']}`")
                    st.dataframe(selected_dataset, use_container_width=True)
                else:
                    st.info("No dataset info found.")

elif st.session_state.explore_reports_dataframe:
    st.dataframe(reports_df[["id", "name", "datasetId", "workspace_name", "Reportstatus Based on Dataset"]])
