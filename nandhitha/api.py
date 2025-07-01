# modules/api.py
import requests

def call_powerbi_api(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def fetch_reports(token, workspace_id):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
    return call_powerbi_api(url, token)

def fetch_datasets(token, workspace_id):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    return call_powerbi_api(url, token)

def fetch_users(token, workspace_id):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
    return call_powerbi_api(url, token)
