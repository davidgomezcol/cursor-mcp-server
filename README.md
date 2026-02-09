# Jira MCP Server

MCP (Model Context Protocol) server that provides Jira issue context to AI assistants like Cursor, VS Code Copilot, Claude Desktop, and Codex.

## Features

- **get_jira_issue** - Fetch full issue details by key
- **get_jira_issue_from_branch** - Extract Jira key from git branch name and fetch details
- **get_jira_comments** - Get comments for an issue
- **test_jira_connection** - Verify Jira API connectivity

Each tool returns:
- Issue summary, description, status, priority, assignee
- **Reproduction steps** (extracted from description)
- **Recent comments** (up to 10)
- Components, labels, and metadata

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Jira account with API token

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd cursor-mcp-server
```

2. Install uv (if not already installed):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

3. Install dependencies:

```bash
uv sync
```

### Environment Variables

Create an `.env` file in the project root:

```env
JIRA_SERVER=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
```

To create a Jira API token:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token and add it to your `.env` file

## Configuration

### Cursor

Add to your Cursor MCP settings (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "jira": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/cursor-mcp-server", "python", "-m", "app.main"]
    }
  }
}
```

### VS Code (Copilot)

Add to your VS Code settings or `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "jira": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/cursor-mcp-server", "python", "-m", "app.main"]
    }
  }
}
```

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "jira": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/cursor-mcp-server", "python", "-m", "app.main"]
    }
  }
}
```

### Codex

Add to your Codex MCP configuration:

```json
{
  "mcpServers": {
    "jira": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/cursor-mcp-server", "python", "-m", "app.main"]
    }
  }
}
```

## Available Tools

### get_jira_issue

Fetch details for a Jira issue by its key.

```
Input: { "issue_key": "PROJ-123" }
Output: {
  "issue_key": "PROJ-123",
  "summary": "Issue title",
  "description": "Full description...",
  "status": "In Progress",
  "priority": "High",
  "assignee": "John Doe",
  "reproduction_steps": "1. Do this\n2. Do that",
  "comments": [...]
}
```

### get_jira_issue_from_branch

Extract Jira key from a git branch name and fetch issue details.

```
Input: { "branch_name": "feature/PROJ-123-add-feature" }
Output: { ... same as get_jira_issue ... }
```

### get_jira_comments

Get comments for a Jira issue.

```
Input: { "issue_key": "PROJ-123", "max_comments": 5 }
Output: {
  "issue_key": "PROJ-123",
  "comment_count": 5,
  "comments": [
    { "author": "Jane Doe", "body": "Comment text...", "created": "..." }
  ]
}
```

### test_jira_connection

Verify Jira API connectivity.

```
Input: {}
Output: {
  "status": "success",
  "connected_as": "John Doe",
  "email": "john@company.com"
}
```

## Development

### Running Locally (for testing)

```bash
uv run python -m app.main
```

### Running Tests

```bash
uv run pytest
```

## Project Structure

```
cursor-mcp-server/
├── app/
│   ├── __init__.py
│   ├── main.py          # MCP server and tool definitions
│   ├── jira_client.py   # Jira API client with caching
│   └── utils.py         # Utility functions
├── pyproject.toml       # Project configuration and dependencies
├── .env                 # Environment variables (not in git)
└── README.md
```
