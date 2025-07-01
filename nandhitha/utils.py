# modules/utils.py
import pandas as pd

def filter_data(reports_data, datasets_data, users_data, domain):
    reports_df = pd.DataFrame(reports_data.get("value", []))
    datasets_df = pd.DataFrame(datasets_data.get("value", []))
    users_df = pd.DataFrame(users_data.get("value", []))

    filtered_datasets_df = datasets_df[datasets_df["configuredBy"].str.endswith(domain, na=False)].copy()
    allowed_dataset_ids = set(filtered_datasets_df["id"].tolist())
    filtered_reports_df = reports_df[reports_df["datasetId"].isin(allowed_dataset_ids)].copy()
    filtered_users_df = users_df[users_df.get("emailAddress", "").str.endswith(domain, na=False)].copy()

    filtered_users_df.drop(columns=['identifier'], errors='ignore', inplace=True)
    filtered_users_df.dropna(subset=['emailAddress'], inplace=True)

    filtered_datasets_df["createdDate"] = pd.to_datetime(filtered_datasets_df["createdDate"], errors="coerce").dt.tz_localize(None)
    cutoff = pd.Timestamp.now() - pd.DateOffset(months=12)
    filtered_datasets_df["outdated"] = filtered_datasets_df["createdDate"] < cutoff
    filtered_datasets_df["datasetStatus"] = filtered_datasets_df["isRefreshable"].apply(lambda x: "Active" if x else "Inactive")

    filtered_reports_df = filtered_reports_df.merge(
        filtered_datasets_df[['id', 'datasetStatus', 'outdated']],
        left_on="datasetId",
        right_on="id",
        how="left"
    )

    filtered_reports_df.drop(columns=['id_y', 'users', 'subscriptions'], errors='ignore', inplace=True)
    filtered_reports_df.rename(columns={"id_x": "id"}, inplace=True)
    filtered_datasets_df.drop(columns=["upstreamDatasets", "users"], errors='ignore', inplace=True)

    filtered_reports_df["reportstatus"] = filtered_reports_df.apply(classify_report, axis=1)

    return filtered_reports_df, filtered_datasets_df, filtered_users_df

def classify_report(row):
    if row['datasetStatus'] == "Inactive":
        return "Inactive"
    elif row['datasetStatus'] == "Active" and row["outdated"]:
        return 'Active (Outdated)'
    elif row['datasetStatus'] == "Active":
        return 'Active'
    return 'Unknown'

def classify_artifact_type(artifact_id, report_ids, dataset_ids):
    if artifact_id in report_ids:
        return "Report"
    elif artifact_id in dataset_ids:
        return "Dataset"
    return "Unknown"
