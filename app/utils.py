import re

def extract_jira_issue_key(branch: str) -> str | None:
    match = re.search(r"([A-Z]+-\d+)", branch)
    return match.group(1) if match else None
