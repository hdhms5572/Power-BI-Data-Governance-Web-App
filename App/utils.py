import requests
import pandas as pd
import streamlit as st


#Optimization: Cached API data loader
@st.cache_data(ttl=3600)
def get_cached_workspace_data(token, workspace_id, user_email):
    return get_filtered_dataframes(token, workspace_id, user_email)

def validate_session():
    if not (st.session_state.get("access_token") and st.session_state.get("workspace_id") and st.session_state.get("user_email")):
        st.warning("❌ Missing access token, workspace ID, or email. Please provide credentials in the main page.")
        st.stop()

def show_workspace():
    names = st.session_state.get("workspace_names")
    if names:
        st.sidebar.markdown("### 📁 Selected Workspaces:")
        for name in names:
            st.sidebar.markdown(f"- **{name}**")
    else:
        st.warning("⚠️ No workspace selected.")
        st.stop()

def apply_sidebar_style():
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #00004d;
            color: #F3F4F6;
            padding: 1.5rem 1rem;
            font-family: 'Segoe UI', 'Inter', sans-serif;
            border-right: 1px solid rgba(255,255,255,0.08);
        }
        [data-testid="stSidebar"] * {
            color: #F3F4F6 !important;
        }
        [data-testid="stSidebar"] a {
            font-weight: 600;
            font-size: 1.05rem;
            color: #F3F4F6 !important;
            text-decoration: none;
            padding: 0.5rem 1rem;
            display: block;
            border-radius: 6px;
            margin-bottom: 0.4rem;
            transition: background 0.3s ease;
        }
        [data-testid="stSidebar"] a:hover {
            background-color: #1F2937 !important;
        }
        ::-webkit-scrollbar-thumb {
            background-color: #4B5563;
            border-radius: 10px;
        }
        ::-webkit-scrollbar {
            width: 6px;
        }
    </style>
    """, unsafe_allow_html=True)

def render_profile_header():
    if st.session_state.get("logged_in"):
        st.markdown("""
            <style>
                .top-right-profile {
                    position: absolute;
                    top: 1rem;
                    right: 1rem;
                    z-index: 1000;
                    text-align: center;
                    font-size: 1.5rem;
                }
                .top-right-profile input {
                    display: none;
                }
                .top-right-profile label {
                    cursor: pointer;
                    border: 2px solid #2563EB;
                    border-radius: 50%;
                    padding: 0.4rem 0.6rem;
                    transition: background-color 0.3s ease, transform 0.2s ease;
                }
                .top-right-profile label:hover {
                    background-color: #2563EB;
                    color: white;
                    transform: scale(1.1);
                }
                .top-right-profile .email-reveal {
                    margin-top: 6px;
                    font-size: 0.8rem;
                    font-weight: 500;
                    color: #1F2937;
                    display: none;
                }
                .top-right-profile input:checked + label + .email-reveal {
                    display: block;
                }
            </style>

            <div class="top-right-profile">
                <input type="checkbox" id="toggleProfile" />
                <label for="toggleProfile">👤</label>
                <div class="email-reveal">{email}</div>
            </div>
        """.replace("{email}", st.session_state.get("user_email", "")), unsafe_allow_html=True)

def call_powerbi_api(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API call failed: {response.status_code} - {response.text}")
        return None

def get_filtered_dataframes(token, workspace_id, user_email):
    reports_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
    datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    users_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"

    reports_data = call_powerbi_api(reports_url, token)
    datasets_data = call_powerbi_api(datasets_url, token)
    users_data = call_powerbi_api(users_url, token)

    if not (reports_data and datasets_data and users_data):
        st.error("Failed to fetch data from API.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    reports_df = pd.DataFrame(reports_data["value"])
    datasets_df = pd.DataFrame(datasets_data["value"])
    users_df = pd.DataFrame(users_data["value"])

    users_df.drop(columns=['identifier'], errors='ignore', inplace=True)
    users_df.dropna(subset=['emailAddress'], inplace=True)

    datasets_df["createdDate"] = pd.to_datetime(datasets_df["createdDate"], errors="coerce").dt.tz_localize(None)
    cutoff = pd.Timestamp.now() - pd.DateOffset(months=12)
    datasets_df["outdated"] = datasets_df["createdDate"] < cutoff
    datasets_df["Dataset Freshness Status"] = datasets_df.apply(
        lambda row: "Up to Date" if row["isRefreshable"] and not row["outdated"]
        else ("Needs Attention" if row["isRefreshable"] and row["outdated"]
        else "Expired"), axis=1
    )

    reports_df = reports_df.merge(
        datasets_df[['id', 'Dataset Freshness Status']],
        left_on="datasetId", right_on="id", how="left"
    )

    reports_df.drop(columns=['id_y', 'users', 'subscriptions'], inplace=True, errors='ignore')
    reports_df.rename(columns={"id_x": "id"}, inplace=True)

    datasets_df.drop(columns=[
        "isOnPremGatewayRequired", "upstreamDatasets", "users", "addRowsAPIEnabled",
        "isEffectiveIdentityRequired", "isEffectiveIdentityRolesRequired", "targetStorageMode",
        "createReportEmbedURL", "qnaEmbedURL", "queryScaleOutSettings"
    ], inplace=True, errors='ignore')

    def classify_report(row):
        status = row.get("Dataset Freshness Status")
        if status == "Expired":
            return "Expired"
        elif status == "Needs Attention":
            return "Needs Attention"
        elif status == "Up to Date":
            return "Up to Date"
        return "Unknown"

    reports_df["Reportstatus Based on Dataset"] = reports_df.apply(classify_report, axis=1)

    return reports_df, datasets_df, users_df

# Shared utility to handle activity file upload
def handle_activity_upload():
    if "activity_df" not in st.session_state:
        uploaded_file = st.file_uploader("📄 Upload Activity CSV", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df["Activity time"] = pd.to_datetime(df["Activity time"], errors="coerce")
            st.session_state["activity_df"] = df
            st.session_state["activity_filename"] = uploaded_file.name
            st.rerun()
        else:
            st.warning("Please upload an activity CSV file to proceed.")
            st.stop()
    else:
        st.success(f"✅ Uploaded: {st.session_state['activity_filename']}")
        if st.button("🔄 Reset Activity CSV"):
            del st.session_state["activity_df"]
            del st.session_state["activity_filename"]
            st.rerun()

    return st.session_state["activity_df"]

def add_logout_button():
    with st.sidebar:
        st.markdown("""
            <style>
            div.stButton > button:first-child {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 0.5em 1em;
                font-size: 16px;
                transition: background-color 0.3s ease;
            }
            div.stButton > button:first-child:hover {
                background-color: #d32f2f;
            }
            </style>
        """, unsafe_allow_html=True)

        if st.session_state.get("access_token"):
            if st.button("🚪 Logout"):
                for key in [
                    "access_token", "user_email", "workspace_ids",
                    "workspace_names", "logged_in", "workspace_options",
                    "activity_df", "activity_filename", "activity_csv"
                ]:
                    st.session_state.pop(key, None)


# Annotate activity status on reports, datasets, users
def apply_activity_status(activity_df, reports_df, datasets_df, users_df):
    activity_df["Activity time"] = pd.to_datetime(activity_df["Activity time"], errors="coerce")
    activity_df = activity_df.sort_values("Activity time")

    workspace_artifact_ids = set(reports_df["id"]).union(set(datasets_df["id"]))
    activity_df = activity_df[activity_df["ArtifactId"].isin(workspace_artifact_ids)]

    cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=3)

    latest_access = activity_df.drop_duplicates(subset="Artifact Name", keep="last")
    latest_access = latest_access.rename(columns={"Activity time": "Latest Activity"})

    artifact_activity_map = dict(zip(latest_access["ArtifactId"], latest_access["Latest Activity"]))

    recent_user_activity = activity_df[activity_df["Activity time"] >= cutoff_date]
    recent_users = recent_user_activity["User email"].dropna().unique()
    recent_artifacts = latest_access["ArtifactId"].unique()

    users_df["activityStatus"] = users_df["emailAddress"].apply(
        lambda x: "Active" if x in recent_users else "Inactive"
    )

    user_latest_activity = (
        activity_df.sort_values("Activity time")
        .drop_duplicates(subset="User email", keep="last")
        .set_index("User email")["Activity time"]
    )
    users_df["Latest Activity Time"] = users_df["emailAddress"].map(user_latest_activity)

    reports_df["Activity Status"] = reports_df["id"].apply(
        lambda x: "Active" if x in recent_artifacts else "Inactive"
    )
    reports_df["Latest Artifact Activity"] = reports_df["id"].map(artifact_activity_map)

    datasets_df["Activity Status"] = datasets_df["id"].apply(
        lambda x: "Active" if x in recent_artifacts else "Inactive"
    )
    datasets_df["Latest Artifact Activity"] = datasets_df["id"].map(artifact_activity_map)

    return activity_df, reports_df, datasets_df, users_df, latest_access
