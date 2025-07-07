import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace
apply_sidebar_style()
show_workspace()


st.markdown("<h1 style='text-align: center;'>📊 Datasets</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Check for required session state values
if not (st.session_state.get("access_token") and st.session_state.get("workspace_id") and st.session_state.get("user_email")):
    st.warning("❌ Missing access token, workspace ID, or email. Please provide credentials in the main page.")
    st.stop()

# Retrieve from session state
token = st.session_state.access_token
workspace = st.session_state.workspace_id
email = st.session_state.user_email

# Fetch data
reports_df, datasets_df, users_df = get_filtered_dataframes(token, workspace, email)

if datasets_df.empty:
    st.warning("📭 No dataset data available or failed to load.")
    st.stop()


# Changing color based on theme base
theme_base = st.get_option("theme.base")
if theme_base == "dark":
    fig_alpha = 0.5
else:
    fig_alpha = 0.01
col1, col2 = st.columns(2)
with col1:
    st.subheader("📓 Dataset Status vs Freshness")
    group = datasets_df.groupby(["datasetStatus", "outdated"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots()
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)   
    ax.title.set_color("gray")
    ax.xaxis.label.set_color("gray")
    ax.yaxis.label.set_color("gray")
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
    ax.set_title("Datasets Created Per Month", color="gray")
    ax.set_ylabel("Count", color="gray")
    ax.set_xlabel("Month", color="gray")
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
    ax.set_title("Dataset Refresh Capability", color="gray")
    ax.set_ylabel("Number of Datasets", color="gray")
    ax.tick_params(colors="gray")
    group.plot(kind="bar", color=["green", "red"], ax=ax)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color("gray")
    st.pyplot(fig)
with col2:
    st.subheader("🌡️ Heatmap: Report vs Dataset Status")
    cross = pd.crosstab(reports_df["Reportstatus Based on Dataset"], reports_df["datasetStatus"])
    fig, ax = plt.subplots(figsize=(4, 3))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)   
    ax.title.set_color("gray")
    ax.xaxis.label.set_color("gray")
    ax.yaxis.label.set_color("gray")
    ax.tick_params(colors="gray")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color("gray")
    sns.heatmap(cross, annot=True, fmt="d", cmap="Blues", ax=ax)
    st.pyplot(fig)




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

    st.markdown(" 🔗 Datasets")
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 3, 2])
        col1.markdown("<h5 style='margin-bottom: 0.5rem;'>🔖 ID</h5>", unsafe_allow_html=True)
        col2.markdown("<h5 style='margin-bottom: 0.5rem;'>📛 Name</h5>", unsafe_allow_html=True)
        col3.markdown("<h5 style='margin-bottom: 0.5rem;'>👤 ConfiguredBy</h5>", unsafe_allow_html=True)
        col4.markdown("<h5 style='margin-bottom: 0.5rem;'>📅 CreatedDate</h5>", unsafe_allow_html=True)
        col5.markdown("<h5 style='margin-bottom: 0.5rem;'>🔍 Explore Dataset</h5>", unsafe_allow_html=True)


    for index, row in datasets_df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 3, 4, 3, 2])
            col1.markdown(f"**{row['id']}**")
            col2.markdown(f"**{row['name']}**")
            col3.markdown(f"`{row['configuredBy']}`")
            col4.write(f"**{row['createdDate']}**")
            col5.markdown(
            f"""<a href="{row['webUrl']}" target="_blank"><button style='font-size: 0.9rem;'>🚀 Explore</button></a>""",
            unsafe_allow_html=True
            )

elif st.session_state.Explore_datasets_dataframe:
    st.dataframe(datasets_df)
