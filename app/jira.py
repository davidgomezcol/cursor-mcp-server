import requests

def fetch_jira_summary(issue_key: str) -> str:
    # Replace with your Jira credentials
    JIRA_BASE_URL = "https://your-domain.atlassian.net"
    JIRA_USER = "your-email@example.com"
    JIRA_TOKEN = "your-api-token"

    try:
        response = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}",
            auth=(JIRA_USER, JIRA_TOKEN),
            headers={"Accept": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            return f"{issue_key}: {data['fields']['summary']}"
        else:
            return f"Could not fetch {issue_key} (HTTP {response.status_code})"
    except Exception as e:
        return f"Error fetching Jira issue: {str(e)}"
