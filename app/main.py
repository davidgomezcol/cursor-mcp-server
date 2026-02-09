import logging
import sys
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from app.jira_client import (
    get_issue_details,
    get_issue_comments,
    get_jira_client,
    JiraClientError,
)
from app.utils import extract_jira_key_from_branch

# Configure logging to stderr (stdout is used by MCP protocol)
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise, only warnings and errors
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create MCP server
mcp = FastMCP("jira")


@mcp.tool()
def get_jira_issue(issue_key: str) -> dict:
    """
    Get details for a Jira issue by its key.
    
    Args:
        issue_key: The Jira issue key (e.g., 'PROJ-123')
        
    Returns:
        Issue details including summary, description, status, priority,
        assignee, reproduction steps, and recent comments.
    """
    try:
        logger.info(f"Fetching Jira issue: {issue_key}")
        issue_details = get_issue_details(issue_key)
        
        if not issue_details:
            return {"error": f"Issue {issue_key} not found"}
        
        return {
            "issue_key": issue_key,
            "summary": issue_details.get("summary"),
            "description": issue_details.get("description"),
            "status": issue_details.get("status"),
            "priority": issue_details.get("priority"),
            "assignee": issue_details.get("assignee"),
            "issuetype": issue_details.get("issuetype"),
            "created": issue_details.get("created"),
            "updated": issue_details.get("updated"),
            "url": issue_details.get("url"),
            "components": issue_details.get("components", []),
            "labels": issue_details.get("labels", []),
            "reproduction_steps": issue_details.get("reproduction_steps"),
            "comments": issue_details.get("comments", []),
        }
    except JiraClientError as e:
        logger.error(f"Jira client error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error fetching Jira issue: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
def get_jira_issue_from_branch(branch_name: str) -> dict:
    """
    Extract Jira issue key from a git branch name and fetch its details.
    
    Supports common branch naming formats:
    - feature/PROJ-123-description
    - bugfix/PROJ-123_fix_something
    - PROJ-123-short-description
    - hotfix/PROJ-123
    
    Args:
        branch_name: The git branch name
        
    Returns:
        Issue details if a Jira key is found in the branch name,
        otherwise an error message.
    """
    jira_key = extract_jira_key_from_branch(branch_name)
    
    if not jira_key:
        return {"error": f"No Jira issue key found in branch name: {branch_name}"}
    
    logger.info(f"Extracted Jira key {jira_key} from branch {branch_name}")
    return get_jira_issue(jira_key)


@mcp.tool()
def get_jira_comments(issue_key: str, max_comments: int = 10) -> dict:
    """
    Get comments for a Jira issue.
    
    Args:
        issue_key: The Jira issue key (e.g., 'PROJ-123')
        max_comments: Maximum number of comments to retrieve (default 10)
        
    Returns:
        List of comments with author, body, and timestamps.
    """
    try:
        logger.info(f"Fetching comments for issue: {issue_key}")
        comments = get_issue_comments(issue_key, max_comments)
        
        return {
            "issue_key": issue_key,
            "comment_count": len(comments),
            "comments": comments,
        }
    except JiraClientError as e:
        logger.error(f"Jira client error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error fetching comments: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
def test_jira_connection() -> dict:
    """
    Test the connection to the Jira API.
    
    Returns:
        Connection status and authenticated user details.
    """
    try:
        jira = get_jira_client()
        myself = jira.myself()
        return {
            "status": "success",
            "connected_as": myself["displayName"],
            "email": myself["emailAddress"],
        }
    except JiraClientError as e:
        logger.error(f"Jira connection test failed: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error testing Jira connection: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
