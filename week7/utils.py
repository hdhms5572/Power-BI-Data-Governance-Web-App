import requests
import pandas as pd
import streamlit as st

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

# # utils.py
# def apply_sidebar_style():
#     st.markdown("""
#     <style>
#         [data-testid="stSidebar"] {
#             background-color: lightblack;
#             padding: 1.5rem 1rem;
#             border-right: 1px solid gray;
#             font-family: 'Segoe UI', 'Inter', sans-serif;
#         }
#         [data-testid="stSidebar"] ul {
#             padding-left: 0;
#         }
#         [data-testid="stSidebar"] ul li a {
#             font-size: 1.05rem !important;
#             font-weight: 600;
#             color: white !important;
#             padding: 0.5rem 0;
#             margin-bottom: 0.4rem;
#             border-radius: 6px;
#             display: block;
#             text-decoration: none;
#         }
#         [data-testid="stSidebar"] ul li a:hover {
#             background-color: lightblack !important;
#         }
#     </style>
#     """, unsafe_allow_html=True)

    
def call_powerbi_api(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API call failed: {response.status_code} - {response.text}")
        return None

def get_filtered_dataframes(token, workspace_id, user_email):
    # URLs
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
   # Classify datasets based on refreshability
    datasets_df["Dataset Freshness Status"] = datasets_df.apply(
    lambda row: "Up to Date" if row["isRefreshable"] and not row["outdated"]
    else ("Needs Attention" if row["isRefreshable"] and row["outdated"]
    else "Expired"), axis=1
)

    # Merge dataset freshness status into reports
    reports_df = reports_df.merge(
        datasets_df[['id', 'Dataset Freshness Status']],
        left_on="datasetId",
        right_on="id",
        how="left"
    )

    # Clean and rename columns
    reports_df.drop(columns=['id_y', 'users', 'subscriptions'], inplace=True, errors='ignore')
    reports_df.rename(columns={"id_x": "id"}, inplace=True)

    # Drop unnecessary columns from datasets
    datasets_df.drop(columns=[
        "isOnPremGatewayRequired", "upstreamDatasets", "users", "addRowsAPIEnabled",
        "isEffectiveIdentityRequired", "isEffectiveIdentityRolesRequired", "targetStorageMode",
        "createReportEmbedURL", "qnaEmbedURL", "queryScaleOutSettings"
    ], inplace=True, errors='ignore')

    # Classify reports based on dataset freshness
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
