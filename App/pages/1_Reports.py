import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace
apply_sidebar_style() 
show_workspace()


st.markdown("<h1 style='text-align: center;'>📄 Reports</h1>", unsafe_allow_html=True)
st.markdown("""<hr>""", unsafe_allow_html=True)

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

if reports_df.empty:
    st.warning("📭 No report data available or failed to load.")
    st.stop()

# Changing color based on theme base
theme_base = st.get_option("theme.base")
if theme_base == "dark":
    fig_alpha = 1.0  
else:
    fig_alpha = 0.01
col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Report Status Count")
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
    sns.countplot(data=reports_df, x="Reportstatus Based on Dataset", palette={"Active": "green", "Inactive": "red", "Active (Outdated)": "orange"}, ax=ax)
    st.pyplot(fig)
with col2:
    st.subheader("🥧 Report Status Share")
    counts = reports_df["Reportstatus Based on Dataset"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)
    ax.title.set_color("gray")
    ax.xaxis.label.set_color("gray")
    ax.yaxis.label.set_color("gray") 
    ax.tick_params(colors="gray")
    wedges, texts, autotexts = ax.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=["green", "red", "orange"], startangle=150,)
    for text in texts:
        text.set_color("gray")
        text.set_fontweight('bold')
    ax.axis("equal")
    st.pyplot(fig)


st.subheader("🔗 Reports per Dataset")
dataset_counts = reports_df['datasetId'].value_counts().reset_index()
dataset_counts.columns = ['datasetId', 'report_count']
top_datasets = dataset_counts.head(10)

fig, ax = plt.subplots(figsize=(7, 4))
fig.patch.set_alpha(fig_alpha)
ax.patch.set_alpha(fig_alpha)
ax.set_title("Top Datasets by Report Count", color='gray')
ax.set_xlabel("Report Count", color='gray')
ax.set_ylabel("Dataset ID", color='gray')
ax.tick_params(colors="gray")
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_color("gray")

sns.barplot(data=top_datasets, x='report_count', y='datasetId', palette='mako', ax=ax)
st.pyplot(fig)




if "view_reports" not in st.session_state:
    st.session_state.view_reports = False
if "explore_reports_dataframe" not in st.session_state:
    st.session_state.explore_reports_dataframe = False

with st.container():
    col1, col2, col3, col4, col5 = st.columns([1,3,3,4,1])
    with col2:
        if st.button("📄 View Reports"):
            st.session_state.view_reports = True
            st.session_state.explore_reports_dataframe = False
    with col4:
        if st.button("📄 Explore Reports DataFrame"):
            st.session_state.view_reports = False
            st.session_state.explore_reports_dataframe = True

    if st.session_state.view_reports:
        
        if "selected_dataset_id" not in st.session_state:
            st.session_state.selected_dataset_id = None

        st.markdown(" 🔗 Reports")
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([5, 3, 2, 3, 2])
            col1.markdown("<h5 style='margin-bottom: 0.5rem;'>🔖 ID</h5>", unsafe_allow_html=True)
            col2.markdown("<h5 style='margin-bottom: 0.5rem;'>📛 Name</h5>", unsafe_allow_html=True)
            col3.markdown("<h5 style='margin-bottom: 0.5rem;'>🥧 Report Status</h5>", unsafe_allow_html=True)
            col4.markdown("<h5 style='margin-bottom: 0.5rem;'>📊 DataSet</h5>", unsafe_allow_html=True)
            col5.markdown("<h5 style='margin-bottom: 0.5rem;'>🔍 Explore Report</h5>", unsafe_allow_html=True)


        for index, row in reports_df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([5, 3, 2, 3, 2])
                col1.markdown(f"`{row['id']}`")
                col2.markdown(f"**{row['name']}**")
                col3.markdown(f"{row.get('Reportstatus Based on Dataset', 'Unknown')}")

                if col4.button("View Dataset", key=f"btn_{row['datasetId']}"):
                    st.session_state.selected_dataset_id = (
                        row['datasetId'] if st.session_state.selected_dataset_id != row['datasetId'] else None
                    )
                col5.markdown(
                    f"""<a href="{row['webUrl']}" target="_blank"><button style='font-size: 0.9rem;'>🚀 Explore</button></a>""",
                    unsafe_allow_html=True
                )
                if st.session_state.selected_dataset_id == row['datasetId']:
                    selected_dataset = datasets_df[datasets_df["id"] == row["datasetId"]]
                    if not selected_dataset.empty:
                        st.markdown(f"##### 📌 Dataset for ID: `{row['datasetId']}`")
                        
                        st.dataframe(selected_dataset, use_container_width=True)
                    else:
                        st.info("⚠️ No dataset found for this report.")

    elif st.session_state.explore_reports_dataframe:
        st.dataframe(reports_df[["id", "name","datasetId","datasetStatus","outdated","Reportstatus Based on Dataset"]])


