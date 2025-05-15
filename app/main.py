from fastapi import FastAPI
from pydantic import BaseModel
from app.utils import extract_jira_issue_key
from app.jira import fetch_jira_summary

app = FastAPI()


class RepoInfo(BaseModel):
    branch: str | None = None


class ContextRequest(BaseModel):
    filePath: str
    selection: str
    repoInfo: RepoInfo | None = None


@app.post("/context")
async def context_provider(data: ContextRequest):
    issue_key = extract_jira_issue_key(data.repoInfo.branch if data.repoInfo else "")
    jira_summary = fetch_jira_summary(issue_key) if issue_key else "No Jira issue found."

    return {
        "context": f"""
You are editing: {data.filePath}
Selection:
{data.selection}

Jira Summary:
{jira_summary}
"""
    }
