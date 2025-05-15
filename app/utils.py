import re
import logging
from typing import Optional, List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def extract_jira_key_from_branch(branch_name: str) -> Optional[str]:
    """
    Extract Jira issue key from the branch name.
    
    Supports common naming formats:
    - feature/PROJ-123-description
    - bugfix/PROJ-123_fix_something
    - PROJ-123-short-description
    - PROJ-123_another_format
    - release/sprint-10/PROJ-123
    - hotfix/PROJ-123
    - chore/PROJ-123-update-deps
    
    Args:
        branch_name: The git branch name
        
    Returns:
        The Jira issue key if found, None otherwise
    """
    # Common pattern for Jira issue keys: 2+ uppercase letters followed by a hyphen and numbers
    pattern = r'([A-Z]{2,}-\d+)'
    match = re.search(pattern, branch_name)
    
    if match:
        key = match.group(1)
        logger.debug(f"Extracted Jira key '{key}' from branch '{branch_name}'")
        return key
    
    logger.debug(f"No Jira key found in branch '{branch_name}'")
    return None

def format_issue_for_context(issue_key: str, issue_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a Jira issue for the Cursor context API
    
    Args:
        issue_key: The Jira issue key
        issue_details: The issue details from Jira API
        
    Returns:
        A formatted dictionary for the context API
    """
    # Create a markdown-formatted content with key details
    content_md = f"""
    # {issue_key}: {issue_details.get('summary', 'No summary')}

    **Type:** {issue_details.get('issuetype', 'Unknown')}  
    **Status:** {issue_details.get('status', 'Unknown')}  
    **Priority:** {issue_details.get('priority', 'Not set')}  
    **Assignee:** {issue_details.get('assignee', 'Unassigned')}

    ## Description
    {issue_details.get('description', 'No description provided')}

    """
    
    # Add components if available
    components = issue_details.get('components', [])
    if components:
        content_md += f"\n**Components:** {', '.join(components)}\n"
    
    # Add labels if available
    labels = issue_details.get('labels', [])
    if labels:
        content_md += f"\n**Labels:** {', '.join(labels)}\n"
    
    # Add link to Jira
    content_md += f"\n[View in Jira]({issue_details.get('url', '')})\n"
    
    return {
        "type": "jira_issue",
        "title": f"{issue_key}: {issue_details.get('summary', 'No summary')}",
        "content": content_md,
        "metadata": {
            "issue_key": issue_key,
            "status": issue_details.get('status', 'Unknown'),
            "priority": issue_details.get('priority', 'Unknown'),
            "assignee": issue_details.get('assignee', 'Unassigned'),
            "issuetype": issue_details.get('issuetype', 'Unknown'),
            "url": issue_details.get('url', '')
        }
    }
