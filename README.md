# Cursor MCP Server (Python + FastAPI)

Custom MCP server to inject Jira issue summaries into Cursor's context API.

## Features

- Parses Jira ticket from branch name
- Queries Jira REST API for summary
- Prepares context for Cursor AI

## Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3000
