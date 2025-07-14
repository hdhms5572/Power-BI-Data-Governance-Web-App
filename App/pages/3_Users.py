import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib
import plotly.express as px
from utils import get_filtered_dataframes, apply_sidebar_style, show_workspace

apply_sidebar_style()
show_workspace()

st.markdown("<h1 style='text-align: center;'>👥 Users</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Validate required session state
if not (st.session_state.get("access_token") and st.session_state.get("workspace_ids") and st.session_state.get("user_email")):
    st.warning("❌ Missing access token or selected workspaces. Please authenticate.")
    st.stop()

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Fetch user data across multiple workspaces
users_df_list = []
for ws_id in workspace_ids:
    _, _, users = get_filtered_dataframes(token, ws_id, email)
    users["workspace_id"] = ws_id
    users["workspace_name"] = workspace_map.get(ws_id, "Unknown")
    users_df_list.append(users)

users_df = pd.concat(users_df_list, ignore_index=True)

if users_df.empty:
    st.warning("📭 No user data found across selected workspaces.")
    st.stop()

# Theme-aware plot styling
fig_alpha = 1.0 if st.get_option("theme.base") == "dark" else 0.01
# 🔢 Display number of users per workspace
st.markdown("## 🧮 Number of Users per Workspace")
workspace_user_counts = users_df["workspace_name"].value_counts().reset_index()
workspace_user_counts.columns = ["Workspace", "Number of Users"]
st.dataframe(workspace_user_counts, use_container_width=True)

col1, col2 = st.columns([4,5])
with col1:
    st.subheader("📊 Group User Access Rights")
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

    fig, ax = plt.subplots(figsize=(4, 3.5))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.3),
        textprops={'fontsize': 8}
    )
    for text in texts + autotexts:
        text.set_color("gray")
    ax.set_title("Group Access Rights", fontsize=10, color="gray")
    ax.axis("equal")
    st.pyplot(fig)

with col2:
    st.subheader("🌍 Workspace Access by Email Domain")
    users_df["Domain"] = users_df["emailAddress"].str.split("@").str[-1]
    domain_counts = users_df["Domain"].value_counts().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(4.2, 3))
    fig.patch.set_alpha(fig_alpha)
    ax.patch.set_alpha(fig_alpha)
    ax.set_title("Access by Email Domain", color="gray")
    sns.barplot(x=domain_counts.values, y=domain_counts.index, palette=["SkyBlue"] * len(domain_counts), ax=ax)
    ax.set_xlabel("User Count", color="gray")
    ax.set_ylabel("Email Domain", color="gray")
    ax.tick_params(colors="gray")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color("gray")
    st.pyplot(fig)

st.subheader("🌐 Email Domain Distribution by Workspace")

users_df["Domain"] = users_df["emailAddress"].str.split("@").str[-1]

treemap_df = (
    users_df.groupby(["workspace_name", "Domain"])
    .size()
    .reset_index(name="User Count")
)

fig = px.treemap(
    treemap_df,
    path=["workspace_name", "Domain"],
    values="User Count",
    color="User Count",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig, use_container_width=True)


# Buttons for displaying user table or dataframe
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
    for ws_name, group in users_df.groupby("workspace_name"):
        group = group.reset_index(drop=True)  
        st.markdown(f"### 📍 Workspace: `{ws_name}` ({len(group)} users)")
        header1, header2, header3, header4, header5, header6 = st.columns([1, 3, 5, 3, 2, 2])
        header1.markdown("🔖 ID")
        header2.markdown("📛 Name")
        header3.markdown("👤 Email")
        header4.markdown("👥 Access Rights")
        header5.markdown("🏷️ Type")
        header6.markdown("🏢 Workspace")

        for idx, row in group.iterrows():
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 5, 3, 2, 2])
                col1.markdown(f"**{idx + 1}**")
                col2.markdown(f"**{row['displayName']}**")
                col3.markdown(f"`{row['emailAddress']}`")
                col4.markdown(f"**{row['groupUserAccessRight']}**")
                col5.markdown(f"**{row['principalType']}**")
                col6.markdown(f"`{row['workspace_name']}`")

elif st.session_state.Explore_users_dataframe:
    st.markdown("## 📊 Full Datasets Table by Workspace")
    for ws_name, group in users_df.groupby("workspace_name"):

        col1, col2 = st.columns([5,1])
        with col1:
            st.markdown(f"### 🏢 Workspace: `{ws_name}`")
        with col2:
            csv = group.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{ws_name}_activity_log.csv",
                mime="text/csv"
            )

        st.dataframe(group[["emailAddress", "groupUserAccessRight", "displayName", "workspace_name"]])
