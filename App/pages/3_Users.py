import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace
apply_sidebar_style()
show_workspace()

st.markdown("<h1 style='text-align: center;'>👥 Users</h1>", unsafe_allow_html=True)
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

if users_df.empty:
    st.warning("📭 No user data available or failed to load.")
    st.stop()

# Group User Access Rights
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


# Changing color based on theme base
theme_base = st.get_option("theme.base")
if theme_base == "dark":
    fig_alpha = 1.0  
else:
    fig_alpha = 0.01
col1, col2 = st.columns([4,5])
with col1:
    st.subheader("📊 Group User Access Rights")
    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)
    ax.set_facecolor("none")

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.3),
        textprops={'fontsize': 8, 'color': 'black'}
    )
    for text in texts + autotexts:
        text.set_color("gray")
    ax.set_title("Group User Access Rights", fontsize=10, color="gray")
    ax.axis("equal")
    st.pyplot(fig)

# Workspace Access by Email Domain
users_df["Domain"] = users_df["emailAddress"].str.split("@").str[-1]
domain_counts = users_df["Domain"].value_counts().sort_values(ascending=True)

with col2:
    st.subheader("🌍 Workspace Access by Email Domain")
    fig, ax = plt.subplots(figsize=(3.3, 2.8))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)
    ax.set_facecolor("none")

    sns.barplot(
        x=domain_counts.values,
        y=domain_counts.index,
        palette=["SkyBlue"] * len(domain_counts),
        ax=ax
    )
    ax.set_title("Workspace Access by Email Domain", fontsize=12, color="white", weight='bold')
    ax.set_xlabel("User Count", fontsize=9, color="gray")
    ax.set_ylabel("Email Domain", fontsize=9, color="gray")
    ax.tick_params(axis='x', labelsize=8, colors="gray")
    ax.tick_params(axis='y', labelsize=8, colors="gray")

    for label in ax.get_yticklabels() + ax.get_xticklabels():
        label.set_color("gray")

    sns.despine()
    st.pyplot(fig)



if "veiw_users" not in st.session_state:
    st.session_state.veiw_users = False
if "Explore_users_dataframe" not in st.session_state:
    st.session_state.Explore_users_dataframe = False

with st.container():
    col1, col2, col3, col4, col5 = st.columns([1,3,3,4,1])
    with col2:
        if st.button("📄 View Users"):
            st.session_state.veiw_users = True
            st.session_state.Explore_users_dataframe = False
    with col4:
        if st.button("📄 Explore Users DataFrame"):
            st.session_state.veiw_users = False
            st.session_state.Explore_users_dataframe = True


if st.session_state.veiw_users:
    # Display user data
    st.markdown(" 🔗 Users")
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([1, 3, 5, 3, 2])
        col1.markdown("<h5 style='margin-bottom: 0.5rem;'>🔖 ID</h5>", unsafe_allow_html=True)
        col2.markdown("<h5 style='margin-bottom: 0.5rem;'>📛 Name</h5>", unsafe_allow_html=True)
        col3.markdown("<h5 style='margin-bottom: 0.5rem;'>👤 EmailAddress</h5>", unsafe_allow_html=True)
        col4.markdown("<h5 style='margin-bottom: 0.5rem;'>👥 Access Rights</h5>", unsafe_allow_html=True)
        col5.markdown("<h5 style='margin-bottom: 0.5rem;'>🏷️ Principal Type</h5>", unsafe_allow_html=True)

    for index, row in users_df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 5, 3, 2])
            col1.markdown(f"**{index+1}**")
            col2.markdown(f"**{row['displayName']}**")
            col3.markdown(f"`{row['emailAddress']}`")
            col4.write(f"**{row['groupUserAccessRight']}**")
            col5.write(f"**{row['principalType']}**")
elif st.session_state.Explore_users_dataframe:
    st.dataframe(users_df[["emailAddress", "groupUserAccessRight","displayName"]])
