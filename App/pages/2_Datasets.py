import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import  render_profile_header
import plotly.express as px
from utils import get_cached_workspace_data, apply_sidebar_style, show_workspace, add_logout_button

apply_sidebar_style()
def inject_external_style():
    with open("static/style.css") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
inject_external_style()

if not (st.session_state.get("access_token") and
        st.session_state.get("user_email")):
    st.warning("🔐 Authentication Required")
    st.stop()

add_logout_button()
render_profile_header()
show_workspace()


col1, col2, col3 = st.columns(3)
with col2:
    st.image("./images/dover_log.png")

st.markdown("<h1 style='text-align: center;'>📊 Datasets</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; font-size: 1.05rem; background-color: #E7DBF3; padding: 14px 24px; border-left: 6px solid #673ab7; border-radius: 8px; margin-bottom: 25px;'>
This dashboard provides an in-depth overview of Power BI datasets available in selected workspaces. 
Track dataset freshness, refreshability, creation trends, and dataset-to-report relationships using visual summaries and interactive tables.
</div><hr>
""", unsafe_allow_html=True)

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

reports_df_list, datasets_df_list, users_df_list = [], [], []

for ws_id in workspace_ids:
    reports, datasets, users = get_cached_workspace_data(token, ws_id, email)
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
    st.warning("📍 No dataset data available.")
    st.stop()

st.session_state.setdefault("dataset_filter_status", None)
st.session_state.setdefault("view_datasets", False)
st.session_state.setdefault("explore_datasets_dataframe", False)

col1, col2, col3,col4 = st.columns(4)
with col1:
    if st.button("🧮 Total Datasets"):
        st.session_state.filter_status = None
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Total Datasets</div><div class='grid-value'>{len(datasets_df)}</div></div>", unsafe_allow_html=True)
with col2:
    if st.button("✅ Up to Date"):
        st.session_state.dataset_filter_status = "Up to Date"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Up to Date</div><div class='grid-value'>{(datasets_df['Dataset Freshness Status'] == 'Up to Date').sum()}</div></div>", unsafe_allow_html=True)

with col3:
    if st.button("⏳ Needs Attention"):
        st.session_state.dataset_filter_status = "Needs Attention"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Needs Attention</div><div class='grid-value'>{(datasets_df['Dataset Freshness Status'] == 'Needs Attention').sum()}</div></div>", unsafe_allow_html=True)

with col4:
    if st.button("🚫 Expired"):
        st.session_state.dataset_filter_status = "Expired"
    st.markdown(f"<div class='grid-card'><div class='grid-title'>Expired</div><div class='grid-value'>{(datasets_df['Dataset Freshness Status'] == 'Expired').sum()}</div></div>", unsafe_allow_html=True)

st.markdown("---")


#VISUALISATIONS
col1, col2 = st.columns(2)
with col1:
    st.header( "📊Refreshable vs Static Datasets")
    datasets_df["RefreshType"] = datasets_df["isRefreshable"].map({True: "Refreshable", False: "Static"})
    datasets_df["hover_info"] = datasets_df["name"]

    grouped = (
        datasets_df
        .groupby(["workspace_name", "RefreshType"])
        .agg(
            Count=("name", "count"),
            DatasetNames=("hover_info", lambda x: "<br>".join(x))
        )
        .reset_index()
    )
    # Total counts
    total_refreshable = (datasets_df["RefreshType"] == "Refreshable").sum()
    total_static = (datasets_df["RefreshType"] == "Static").sum()
    st.write(f"✅ Refreshable Datasets: {total_refreshable}",f"🚫 Static Datasets: {total_static}")

    fig = px.bar(
        grouped,
        x="workspace_name",
        y="Count",
        color="RefreshType",
        text="Count",
        hover_data={"DatasetNames": True, "Count": False, "RefreshType": True},
        barmode="group",
        color_discrete_map={"Refreshable": "#4CAF50", "Static": "#F44336"},
        
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.header("📅 Dataset Creation Timeline")
    datasets_df["createdDate"] = pd.to_datetime(datasets_df["createdDate"], errors="coerce")
    datasets_df["createdTime"] = datasets_df["createdDate"].dt.to_period("M").astype(str)
    datasets_df["hover_info"] = datasets_df["name"] + " (" + datasets_df["workspace_name"] + ")"

    # Group and summarize
    grouped = datasets_df.groupby("createdTime").agg({
        "name": "count",
        "hover_info": lambda x: "<br>".join(x)
    }).rename(columns={"name": "Count", "hover_info": "Dataset Details"}).reset_index()

    # Plotly line chart
    fig = px.line(
        grouped,
        x="createdTime",
        y="Count",
        text="Count",
        markers=True,
        hover_data={"Dataset Details": True, "Count": False},
        
    )

    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)
        

st.subheader("📊 Dataset Freshness Status")

if "show_dataset_description" not in st.session_state:
    st.session_state["show_dataset_description"] = False

if st.button("ℹ️ Chart Info", key="dataset_info"):
    st.session_state["show_dataset_description"] = not st.session_state["show_dataset_description"]

if st.session_state["show_dataset_description"]:
    st.markdown("""
    <div style='background-color: #f3f0ff; padding: 12px 20px; border-left: 5px solid #009688; border-radius: 6px; font-size: 0.95rem; margin-bottom: 10px;'>
    <b>Chart Description:</b><br>
    This visualization displays the freshness status of datasets across workspaces. Each bar represents a workspace, segmented by:
    <ul style="padding-left: 18px;">
      <li><span style="color:green;"><b>Up to Date</b></span> – Refreshable datasets created within the last 12 months.</li>
      <li><span style="color:orange;"><b>Needs Attention</b></span> – Refreshable but older than 12 months.</li>
      <li><span style="color:red;"><b>Expired</b></span> – Not refreshable or deprecated datasets.</li>
      <li><span style="color:#a6a6a6;"><b>Unknown</b></span> – Status could not be determined or missing.</li>
    </ul>
    Hover over bar segments to reveal the list of dataset names and their count.
    </div>
    """, unsafe_allow_html=True)

health_data = datasets_df.groupby(["workspace_name", "Dataset Freshness Status"])["name"].agg(list).reset_index()
health_data["Count"] = health_data["name"].apply(len)
health_data["Dataset Names"] = health_data["name"].apply(lambda x: "<br>".join(x))

dataset_status_colors = {
    "Up to Date": "#87CEEB",          
    "Needs Attention": "#E2C312",          
    "Expired": "#F44336",         
    "Unknown": "#a6a6a6",          
}
fig = px.bar(
    health_data,
    x="workspace_name",
    y="Count",
    color="Dataset Freshness Status",
    text="Count",
    color_discrete_map=dataset_status_colors,
    hover_data={"Dataset Names": True, "Count": True, "workspace_name": False, "name": False},
    labels={"workspace_name": "Workspace", "Count": "Number of Datasets"},
    title="Dataset Freshness Status by Workspace"
)

fig.update_layout(barmode="stack", xaxis_tickangle=-45)

st.plotly_chart(fig, use_container_width=True)

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


display_cols = ["name", "configuredBy", "isRefreshable", "createdDate", "outdated", "Dataset Freshness Status"]

# Filtered View
if st.session_state.dataset_filter_status:
    st.markdown(f"##  Filtered Datasets: `{st.session_state.dataset_filter_status}`")
    
    # Apply dataset status filter
    if st.session_state.dataset_filter_status == "Outdated":
        filtered_df = datasets_df[datasets_df["outdated"] == True]
    else:
        filtered_df = datasets_df[datasets_df["Dataset Freshness Status"] == st.session_state.dataset_filter_status]

    # Count by workspace
    ws_counts = filtered_df["workspace_name"].value_counts().reset_index()
    ws_counts.columns = ["Workspace", "Count"]
    st.markdown("### 🧮 Count by Workspace")
    st.dataframe(ws_counts, use_container_width=True)

    # Display filtered datasets per workspace
    for ws_name, group in filtered_df.groupby("workspace_name"):
        st.markdown(f"###  Workspace: `{ws_name}` ({len(group)} datasets)")
        group = group[display_cols + ["webUrl"]]  # Keep webUrl for Explore button

        st.markdown('<div class="classic-table">', unsafe_allow_html=True)
        st.markdown('<div class="classic-row header">', unsafe_allow_html=True)
        header1, header2, header3, header4, header5, header6 = st.columns([3, 4, 2, 2, 2, 2])
        header1.markdown("**Name**")
        header2.markdown("**By**")
        header3.markdown("**Created Date**")
        header4.markdown("**Status**")
        header5.markdown("**Refreshable**")
        header6.markdown("**🔍 Link**")

        for _, row in group.iterrows():
            st.markdown('<div class="classic-row">', unsafe_allow_html=True)
            col1, col2, col3, col4, col5, col6 = st.columns([3, 4, 2, 2, 2, 2])
            col1.markdown(f"**{row['name']}**")
            col2.markdown(row["configuredBy"])
            col3.markdown(str(row["createdDate"]))
            col4.markdown(row["Dataset Freshness Status"])
            col5.markdown("✅ Yes" if row["isRefreshable"] else "❌ No")
            col6.markdown(f"""<a href="{row['webUrl']}" target="_blank">
                <button style='font-size: 0.8rem;'>🚀 Explore</button></a>""", unsafe_allow_html=True)

# View Datasets (Grouped)
elif st.session_state.view_datasets:
    st.markdown("## 🗂️ Datasets Overview by Workspace")

    for ws_name, group in datasets_df.groupby("workspace_name"):
        group = group[display_cols + ["webUrl"]]  # Removed "id"

        st.markdown(f"### 🏢 Workspace: `{ws_name}` ({len(group)} datasets)")

        st.markdown('<div class="classic-table">', unsafe_allow_html=True)
        st.markdown('<div class="classic-row header">', unsafe_allow_html=True)
        header1, header2, header3, header4, header5, header6 = st.columns([3, 3, 2.5, 2.5, 1.5, 2])
        header1.markdown("**Name**")
        header2.markdown("**Configured By**")
        header3.markdown("**Created Date**")
        header4.markdown("**Status**")
        header5.markdown("**Refreshable**")
        header6.markdown("**Actions**")

        for _, row in group.iterrows():
            with st.container():
                st.markdown('<div class="classic-row">', unsafe_allow_html=True)
                col1, col2, col3, col4, col5, col6 = st.columns([3, 3, 2.5, 2.5, 1.5, 2])
                col1.markdown(f"**{row['name']}**")

                configured_by = row.get("configuredBy", "")
                if "@" in configured_by:
                    email_link = f"[{configured_by}](mailto:{configured_by})"
                    col2.markdown(email_link)
                else:
                    col2.markdown(configured_by)

                col3.markdown(str(row["createdDate"]))
                col4.markdown(row["Dataset Freshness Status"])
                col5.markdown("✅" if row["isRefreshable"] else "❌")
                col6.markdown(f"""<a href="{row['webUrl']}" target="_blank">
                    <button style='font-size:0.75rem;'>🚀 Explore</button></a>""", unsafe_allow_html=True)


# Explore DataFrame View
elif st.session_state.explore_datasets_dataframe:
    st.markdown("## 📊 Full Datasets Table by Workspace")

    for ws_name, group in datasets_df.groupby("workspace_name"):
        renamed_df = ( group[display_cols].rename(columns={
        "name": "Name",
        "configuredBy": "Configured By",
        "isRefreshable": "Refreshable",
        "createdDate": "Created Date",
        "outdated": "Outdated",
        "Dataset Freshness Status": "Status"
    })[["Name", "Configured By", "Refreshable", "Created Date", "Outdated", "Status"]]
    .reset_index(drop=True))

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"### 🏢 Workspace: `{ws_name}`")
        with col2:
            csv = renamed_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{ws_name}_datasets.csv",
                mime="text/csv"
            )

        st.dataframe(renamed_df, use_container_width=True)
