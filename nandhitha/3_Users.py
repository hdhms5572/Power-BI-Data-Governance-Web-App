import streamlit as st
from utils import call_powerbi_api, get_filtered_dataframes
from utils import apply_sidebar_style
apply_sidebar_style()
from utils import show_workspace_header
show_workspace_header()
import matplotlib.pyplot as plt
import seaborn as sns


st.title("👥 Users")

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

if users_df.empty:
    st.warning("📭 No user data available or failed to load.")
    st.stop()

# Display user data
st.dataframe(users_df[["displayName", "emailAddress", "groupUserAccessRight", "principalType"]])

# Count users by group access right
role_counts = users_df["groupUserAccessRight"].value_counts()
labels = role_counts.index
sizes = role_counts.values


role_colors = {
    "Admin": "OrangeRed",
    "Contributor": "DodgerBlue",
    "Viewer": "DimGray",
    "Member": "MediumSeaGreen"
}
colors = [role_colors.get(role, "LightGray") for role in labels]

col_left, col_center, col_right = st.columns([1, 2, 1])  

with col_center:
    fig, ax = plt.subplots(figsize=(3.5, 3.5))  
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.3),
        textprops={'fontsize': 8, 'color': 'black'}
    )
    ax.set_title("Group User Access Rights", fontsize=10)
    ax.axis("equal")
    st.pyplot(fig)

# Extract domain names
users_df["Domain"] = users_df["emailAddress"].str.split("@").str[-1]
domain_counts = users_df["Domain"].value_counts().sort_values(ascending=True)  

col_left, col_chart, col_right = st.columns([1, 3, 1])

with col_chart:
    fig, ax = plt.subplots(figsize=(4.8, 2.8))  
    sns.barplot(
        x=domain_counts.values,   #  X-axis: Count
        y=domain_counts.index,    # Y-axis: Email Domain
        palette=["SkyBlue"] * len(domain_counts),
        ax=ax
    )
    ax.set_title("Workspace Access by Email Domain", fontsize=12, weight='bold')
    ax.set_xlabel("User Count", fontsize=9)
    ax.set_ylabel("Email Domain", fontsize=9)
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=8)
    sns.despine()
    st.pyplot(fig)
