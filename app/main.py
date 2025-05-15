from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
from dotenv import load_dotenv

from app.jira import get_issue_details, get_jira_client, JiraClientError
from app.utils import extract_jira_key_from_branch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Cursor MCP Server for Jira",
    description="Custom MCP server to inject Jira issue summaries into Cursor's context API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContextRequest(BaseModel):
    branch: Optional[str] = None
    files: Optional[List[str]] = None
    
class ContextResponse(BaseModel):
    context: List[Dict[str, Any]]

@app.get("/")
async def root():
    return {"message": "Cursor MCP Server for Jira is running"}

@app.get("/context", response_model=ContextResponse)
async def get_context_get():
    """Handle GET requests to the context endpoint"""
    logger.info("Received GET request to /context")
    return {"context": []}

@app.post("/context", response_model=ContextResponse)
async def get_context(request: ContextRequest):
    context_items = []
    
    # Process branch information if provided
    if request.branch:
        logger.info(f"Processing branch: {request.branch}")
        jira_key = extract_jira_key_from_branch(request.branch)
        
        if jira_key:
            logger.info(f"Found Jira key: {jira_key}")
            try:
                issue_details = get_issue_details(jira_key)
                if issue_details:
                    context_items.append({
                        "type": "jira_issue",
                        "title": f"{jira_key}: {issue_details.get('summary', 'No summary')}",
                        "content": issue_details.get('description', 'No description'),
                        "metadata": {
                            "issue_key": jira_key,
                            "status": issue_details.get('status', 'Unknown'),
                            "priority": issue_details.get('priority', 'Unknown'),
                            "assignee": issue_details.get('assignee', 'Unassigned'),
                            "url": issue_details.get('url', '')
                        }
                    })
                    logger.info(f"Added context for issue {jira_key}")
                else:
                    logger.warning(f"No details found for issue {jira_key}")
            except JiraClientError as e:
                logger.error(f"Jira client error: {str(e)}")
            except Exception as e:
                logger.error(f"Error fetching Jira details: {str(e)}")
    else:
        logger.info("No branch information provided in request")
    
    return {"context": context_items}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/test-jira-connection")
async def test_jira_connection():
    """Test the connection to Jira API"""
    try:
        jira = get_jira_client()
        myself = jira.myself()
        return {
            "status": "success", 
            "connected_as": myself["displayName"],
            "email": myself["emailAddress"],
            "server": os.getenv("JIRA_SERVER")
        }
    except JiraClientError as e:
        logger.error(f"Jira connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Jira connection error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error testing Jira connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3000"))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
