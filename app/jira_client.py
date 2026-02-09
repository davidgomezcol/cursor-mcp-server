import os
import re
import time
import logging
from typing import Dict, Any, Optional, List
from functools import lru_cache
from jira import JIRA
from jira.exceptions import JIRAError
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Jira server configuration
JIRA_SERVER = os.getenv("JIRA_SERVER")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

# Cache time-to-live in seconds (5 minutes)
CACHE_TTL = 300

class JiraClientError(Exception):
    """Custom exception for Jira client errors"""
    pass

def get_jira_client() -> JIRA:
    """
    Create and return a Jira client using environment variables for authentication.
    
    Returns:
        JIRA: Authenticated Jira client
        
    Raises:
        JiraClientError: If authentication fails or configuration is missing
    """
    if not all([JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN]):
        raise JiraClientError("Missing Jira configuration. Please check your environment variables.")
    
    try:
        return JIRA(
            server=JIRA_SERVER,
            basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
        )
    except JIRAError as e:
        logger.error(f"JIRA authentication error: {str(e)}")
        raise JiraClientError(f"Could not authenticate with Jira: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating Jira client: {str(e)}")
        raise JiraClientError(f"Unexpected error: {str(e)}")


def extract_reproduction_steps(description: str) -> Optional[str]:
    """
    Extract reproduction steps from a Jira issue description.
    
    Looks for common patterns like:
    - "Steps to Reproduce"
    - "Reproduction Steps"
    - "How to Reproduce"
    - "STR:" or "Steps:"
    
    Args:
        description: The issue description text
        
    Returns:
        The reproduction steps if found, None otherwise
    """
    if not description:
        return None
    
    # Common patterns for reproduction steps sections
    patterns = [
        r'(?:^|\n)\s*(?:#+\s*)?(?:steps?\s*to\s*reproduce|reproduction\s*steps?|how\s*to\s*reproduce|str|steps?)[\s:]*\n?(.*?)(?=\n\s*(?:#+\s*)?(?:expected|actual|environment|notes?|additional|workaround|acceptance|screenshot|attach)|$)',
        r'(?:^|\n)\s*\*?\*?(?:steps?\s*to\s*reproduce|reproduction\s*steps?|how\s*to\s*reproduce)\*?\*?[\s:]*\n?(.*?)(?=\n\s*\*?\*?(?:expected|actual|environment|notes?|additional|workaround|acceptance|screenshot|attach)|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
        if match:
            steps = match.group(1).strip()
            if steps:
                return steps
    
    return None


def get_issue_comments(issue_key: str, max_comments: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve comments for a specific Jira issue.
    
    Args:
        issue_key: The Jira issue key (e.g., 'PROJ-123')
        max_comments: Maximum number of comments to retrieve (default 10)
        
    Returns:
        A list of comment dictionaries with author, body, and created date
        
    Raises:
        JiraClientError: If there is an error communicating with Jira
    """
    try:
        jira = get_jira_client()
        issue = jira.issue(issue_key, fields='comment')
        comments = issue.fields.comment.comments
        
        result = []
        # Get the most recent comments (up to max_comments)
        for comment in comments[-max_comments:]:
            result.append({
                "author": comment.author.displayName if hasattr(comment, 'author') and comment.author else "Unknown",
                "body": comment.body or "",
                "created": comment.created if hasattr(comment, 'created') else None,
                "updated": comment.updated if hasattr(comment, 'updated') else None,
            })
        
        return result
    except JIRAError as e:
        logger.error(f"JIRA error retrieving comments for {issue_key}: {str(e)}")
        if e.status_code == 404:
            return []
        raise JiraClientError(f"JIRA API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error retrieving comments for {issue_key}: {str(e)}")
        raise JiraClientError(f"Unexpected error retrieving comments: {str(e)}")

# Use LRU cache to avoid repeated requests for the same issue
@lru_cache(maxsize=100)
def get_issue_details_cached(issue_key: str, timestamp: int) -> Optional[Dict[str, Any]]:
    """
    Cached version of get_issue_details. The timestamp parameter is used to invalidate 
    the cache after CACHE_TTL seconds.
    """
    try:
        jira = get_jira_client()
        issue = jira.issue(issue_key)
        
        # Extract relevant fields
        assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
        description = issue.fields.description or "No description provided"
        
        # Extract reproduction steps from description
        reproduction_steps = extract_reproduction_steps(description)
        
        # Get comments for the issue
        comments = get_issue_comments(issue_key)
        
        return {
            "summary": issue.fields.summary,
            "description": description,
            "status": issue.fields.status.name,
            "priority": issue.fields.priority.name if issue.fields.priority else "Not set",
            "assignee": assignee,
            "created": issue.fields.created,
            "updated": issue.fields.updated,
            "url": f"{JIRA_SERVER}/browse/{issue_key}",
            "issuetype": issue.fields.issuetype.name,
            "components": [c.name for c in issue.fields.components] if hasattr(issue.fields, 'components') else [],
            "labels": issue.fields.labels if hasattr(issue.fields, 'labels') else [],
            "reproduction_steps": reproduction_steps,
            "comments": comments,
        }
    except JIRAError as e:
        logger.error(f"JIRA error retrieving issue {issue_key}: {str(e)}")
        if e.status_code == 404:
            logger.warning(f"Issue {issue_key} not found")
            return None
        raise JiraClientError(f"JIRA API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error retrieving Jira issue {issue_key}: {str(e)}")
        raise JiraClientError(f"Unexpected error retrieving issue: {str(e)}")

def get_issue_details(issue_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve details for a specific Jira issue by its key.
    
    Args:
        issue_key: The Jira issue key (e.g., 'PROJ-123')
        
    Returns:
        A dictionary containing issue details or None if the issue cannot be found
        
    Raises:
        JiraClientError: If there is an error communicating with Jira
    """
    # Use the current timestamp divided by CACHE_TTL to invalidate cache after the TTL
    cache_timestamp = int(time.time() / CACHE_TTL)
    return get_issue_details_cached(issue_key, cache_timestamp)

def get_project_issues(project_key: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Get a list of issues for a specific project
    
    Args:
        project_key: Project key (e.g., 'PROJ')
        max_results: Maximum number of results to return
        
    Returns:
        List of issue dictionaries
        
    Raises:
        JiraClientError: If there is an error communicating with Jira
    """
    try:
        jira = get_jira_client()
        issues = jira.search_issues(f'project = "{project_key}" ORDER BY updated DESC', maxResults=max_results)
        
        result = []
        for issue in issues:
            assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
            result.append({
                "key": issue.key,
                "summary": issue.fields.summary,
                "status": issue.fields.status.name,
                "assignee": assignee,
                "issuetype": issue.fields.issuetype.name,
                "updated": issue.fields.updated
            })
        return result
    except JIRAError as e:
        logger.error(f"JIRA error retrieving project issues: {str(e)}")
        raise JiraClientError(f"JIRA API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error retrieving project issues: {str(e)}")
        raise JiraClientError(f"Unexpected error retrieving project issues: {str(e)}")
