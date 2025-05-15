# Cursor MCP Server (Python + FastAPI)

Custom MCP server to inject Jira issue summaries into Cursor's context API.

## Features

- Parses Jira ticket from branch name
- Queries Jira REST API for summary and details
- Prepares context for Cursor AI
- Provides connection testing and health endpoints
- Includes caching to minimize Jira API requests

## Setup

### Prerequisites

- Python 3.11+
- Jira account with API token

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cursor-mcp-server
```

### Setup Server and Environment Variables

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install required dependencies
```
pip install -r requirements.txt
```

3. Create an `.env` file with the following variables:
```
# Jira configuration
JIRA_SERVER=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Server configuration
PORT=3000
LOG_LEVEL=INFO
```

## Cursor Configuration

### Setting up the MCP Server in Cursor

1. Open Cursor and go to **Settings**
2. Navigate to the **Plugins** or **Extensions** section
3. Find the MCP configuration section
4. Add the following JSON configuration:

```json
{
  "mcpServers": {
    "jira": {
      "url": "http://localhost:3000/context",
      "enabled": true,
      "description": "Jira issue context provider"
    }
  }
}
