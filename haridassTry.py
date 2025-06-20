import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Input fields in the Streamlit sidebar
st.sidebar.title("Power BI API Settings")
access_token = st.sidebar.text_input("Access Token", type="password")
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSIsImtpZCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSJ9.eyJhdWQiOiJodHRwczovL2FuYWx5c2lzLndpbmRvd3MubmV0L3Bvd2VyYmkvYXBpIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvM2QyZDJiNmYtMDYxYS00OGI2LWI0YjMtOTMxMmQ2ODdlM2ExLyIsImlhdCI6MTc1MDMyMTQyMCwibmJmIjoxNzUwMzIxNDIwLCJleHAiOjE3NTAzMjY2NzEsImFjY3QiOjAsImFjciI6IjEiLCJhaW8iOiJBVVFBdS84WkFBQUFUMjUzaVRqNTJyUTNxRkdEZkE1b2xQY3BIcE5HRUtQMXJBVTRGdWRkOXI4L2x6WFVWdjF1eEw0UG1LKzVqVDViRWJFQitJNUt1ZjVpUVkwL1Y1bU5yUT09IiwiYW1yIjpbInB3ZCIsInJzYSJdLCJhcHBpZCI6IjE4ZmJjYTE2LTIyMjQtNDVmNi04NWIwLWY3YmYyYjM5YjNmMyIsImFwcGlkYWNyIjoiMCIsImRldmljZWlkIjoiN2JjZTMzOGQtZTc4Yi00NDI1LThmZDMtYmFiZjgxYWFhNDhiIiwiZmFtaWx5X25hbWUiOiJTIiwiZ2l2ZW5fbmFtZSI6IkhhcmlkYXNzIChDb250cmFjdG9yKSIsImlkdHlwIjoidXNlciIsImlwYWRkciI6IjE2Ny4xMDMuMjEuMCIsIm5hbWUiOiJTLCBIYXJpZGFzcyAoQ29udHJhY3RvcikiLCJvaWQiOiJjNWQ1NDkwMy1lMDk4LTRkNGEtYWUyNS0wNWQyODM2YmE1NjkiLCJvbnByZW1fc2lkIjoiUy0xLTUtMjEtMjE4NDg0MzA4MC0xNTc0MzU3NzkwLTM2MjM2MDY1MDAtNDc0MzQ5IiwicHVpZCI6IjEwMDMyMDA0QTQ1NDYzNjIiLCJyaCI6IjEuQVFNQWJ5c3RQUm9HdGtpMHM1TVMxb2Zqb1FrQUFBQUFBQUFBd0FBQUFBQUFBQUFEQUtJREFBLiIsInNjcCI6IkFwcC5SZWFkLkFsbCBDYXBhY2l0eS5SZWFkLkFsbCBDYXBhY2l0eS5SZWFkV3JpdGUuQWxsIENvbm5lY3Rpb24uUmVhZC5BbGwgQ29ubmVjdGlvbi5SZWFkV3JpdGUuQWxsIENvbnRlbnQuQ3JlYXRlIERhc2hib2FyZC5SZWFkLkFsbCBEYXNoYm9hcmQuUmVhZFdyaXRlLkFsbCBEYXRhZmxvdy5SZWFkLkFsbCBEYXRhZmxvdy5SZWFkV3JpdGUuQWxsIERhdGFzZXQuUmVhZC5BbGwgRGF0YXNldC5SZWFkV3JpdGUuQWxsIEdhdGV3YXkuUmVhZC5BbGwgR2F0ZXdheS5SZWFkV3JpdGUuQWxsIEl0ZW0uRXhlY3V0ZS5BbGwgSXRlbS5FeHRlcm5hbERhdGFTaGFyZS5BbGwgSXRlbS5SZWFkV3JpdGUuQWxsIEl0ZW0uUmVzaGFyZS5BbGwgT25lTGFrZS5SZWFkLkFsbCBPbmVMYWtlLlJlYWRXcml0ZS5BbGwgUGlwZWxpbmUuRGVwbG95IFBpcGVsaW5lLlJlYWQuQWxsIFBpcGVsaW5lLlJlYWRXcml0ZS5BbGwgUmVwb3J0LlJlYWRXcml0ZS5BbGwgUmVwcnQuUmVhZC5BbGwgU3RvcmFnZUFjY291bnQuUmVhZC5BbGwgU3RvcmFnZUFjY291bnQuUmVhZFdyaXRlLkFsbCBUYWcuUmVhZC5BbGwgVGVuYW50LlJlYWQuQWxsIFRlbmFudC5SZWFkV3JpdGUuQWxsIFVzZXJTdGF0ZS5SZWFkV3JpdGUuQWxsIFdvcmtzcGFjZS5HaXRDb21taXQuQWxsIFdvcmtzcGFjZS5HaXRVcGRhdGUuQWxsIFdvcmtzcGFjZS5SZWFkLkFsbCBXb3Jrc3BhY2UuUmVhZFdyaXRlLkFsbCIsInNpZCI6IjAwNWJlMzg5LTEzZjUtNDlhMC01NTBlLWRiY2VlYTZmMWE0ZSIsInNpZ25pbl9zdGF0ZSI6WyJkdmNfbW5nZCIsImR2Y19jbXAiLCJkdmNfZG1qZCIsImlua25vd25udHdrIiwia21zaSJdLCJzdWIiOiJGeXBJZ2Q2WG81N1hQa0tMS1Y4LU01WTVETEpuQzRqTERLQ0ZaX1pWQzY4IiwidGlkIjoiM2QyZDJiNmYtMDYxYS00OGI2LWI0YjMtOTMxMmQ2ODdlM2ExIiwidW5pcXVlX25hbWUiOiJjLWhzQGRvdmVyY29ycC5jb20iLCJ1cG4iOiJjLWhzQGRvdmVyY29ycC5jb20iLCJ1dGkiOiJUcHFKT04zUUcwdWxXanFuUFlYS0FBIiwidmVyIjoiMS4wIiwid2lkcyI6WyJiNzlmYmY0ZC0zZWY5LTQ2ODktODE0My03NmIxOTRlODU1MDkiXSwieG1zX2Z0ZCI6ImlWOHNZY1hvU0hzLWZ0ZTBDMmhCMi1UUE56N3ppZ294dW9ULTRwRVNzTjRCZFhOemIzVjBhQzFrYzIxeiIsInhtc19pZHJlbCI6IjEgMjYifQ.LpJxS59AFXmTp_BwslwIB4hF_MrEXyfXdXmk3PbV2Q097aTPxQMDuucn7EFoawNvAWUf4fheCHZtiZJLNKo2KN9D9KA2VBKDEo_jHQI73z2M91zLnvhGAIMVZDSd1J21siqZP1XCQkfm_S6qZxUkEpxi-LX6ALdEvETnZzMaLeU2nx7IDfRVoKSyz6aI3QXJ1sivDyllQWQepMkD-lWskRLAUUdDypX9f7InGhfj9SmlhSXWAurlhMvKIu4TNJFFw03e92kOa-PE7SK6zayeMcfglLq0uwm8HZSOQNRyPtEaTmGD8eYdOvtjNkl_Jhzz8onOniMCoEUUfRTFT4lH9A"
workspace_id = st.sidebar.text_input("Workspace ID", value="cf7a33dd-365c-465d-b3a6-89cd2a3ef08c")

# API call function (unchanged)
def call_powerbi_api(url, token):
    headers = { 
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers = {
        "Authorization": f"Bearer {token}"
    })
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API call failed: {response.status_code} - {response.text}")
        return None

# Main logic only runs when token is present

if access_token and workspace_id=="cf7a33dd-365c-465d-b3a6-89cd2a3ef08c":
    reports_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
    datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    users_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"

    reports_data = call_powerbi_api(reports_url, access_token)
    datasets_data = call_powerbi_api(datasets_url, access_token)
    users_data = call_powerbi_api(users_url, access_token)

    def getFilteredData(objects,isfromPbix):
        resObjects = []
        for obj in objects:
            if obj['isFromPbix'] == isfromPbix:
                resObjects.append(obj)
        return resObjects
    
        
    if reports_data and datasets_data and users_data:

        def filterReportsData(reports_data,isfromPbix):
            resObjects = []
            for data in reports_data:
                if data['isFromPbix'] == isfromPbix:
                    resObjects.append(data)
            return resObjects
        


        st.title("Power BI Workspace Overview")

        if st.button("Veiw Reports details"):
            # isfromPbix = st.checkbox("fromPbix")
            filterData = getFilteredData(reports_data["value"],True)
            reports_df = pd.DataFrame(filterData)
            st.subheader("📄 Reports")
            st.write(reports_df)

            # st.subheader("Bar chart for Active and Inactive users")
            # fig_

        if st.button("Veiw Datasets details"):
            datasets_df = pd.DataFrame(datasets_data["value"])
            st.subheader("📊 Datasets")
            st.write(datasets_df)
            st.write(datasets_data)
            st.write("Number of Datasets vs Effective Identity Required")
            # fig_Effic


        if st.button("Veiw User details"):
            users_df = pd.DataFrame(users_data["value"])
            st.subheader("👥 Users")
            st.write(users_df)

            st.subheader("Access Rights Distribution")
            fig_access = px.pie(users_df, names="groupUserAccessRight", title="Access Rights Breakdown")
            st.plotly_chart(fig_access, use_container_width=True)
    else:
        st.warning("Could not fetch all data. Please check your token and workspace ID.")
else:
    st.info("Enter your access token and workspace ID in the sidebar to begin.")

