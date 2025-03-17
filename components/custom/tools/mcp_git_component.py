from langflow.custom import Component
from langflow.io import StrInput, Output, UrlInput
from langflow.schema import Data
import json
import requests

class MCPGitComponent(Component):
    display_name = "MCP Git Component"
    description = "MCP server integration with Git diff analysis"
    icon = "🧠"
    category = "Tools"
    name = "MCPGitComponent"

    def build(self):
        # Server URL input
        self.add_input(
            StrInput(
                id="server_url",
                name="MCP Server URL",
                description="URL of the MCP server",
                default="http://localhost:8000",
                required=True
            )
        )
        
        # Git repository URL input
        self.add_input(
            StrInput(
                id="repo_url",
                name="Repository URL",
                description="URL of the Git repository",
                default="https://github.com/username/repo",
                required=True
            )
        )
        
        # Commit SHA input
        self.add_input(
            StrInput(
                id="commit_sha",
                name="Commit SHA",
                description="SHA of the commit to analyze",
                default="",
                required=True
            )
        )
        
        # Result output
        self.add_output(
            Output(
                id="result",
                name="Result",
                description="Git diff analysis result"
            )
        )
    
    def process(self, data: Data) -> dict:
        server_url = data["inputs"].get("server_url", "http://localhost:8000")
        repo_url = data["inputs"].get("repo_url", "")
        commit_sha = data["inputs"].get("commit_sha", "")
        
        try:
            # Validate inputs
            if not repo_url:
                return {"result": "Error: Repository URL is required for Git diff analysis"}
            
            if not commit_sha:
                return {"result": "Error: Commit SHA is required for Git diff analysis"}
            
            # Construct the API endpoint for git diff analysis
            url = f"{server_url}/v1/models/git-diff-analyzer/analyze"
            
            # Prepare the payload
            payload = {
                "repo_url": repo_url,
                "commit_sha": commit_sha
            }
            
            # Make the API call
            response = requests.post(url, json=payload, timeout=30)
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                return {"result": json.dumps(result, indent=2)}
            else:
                return {"result": f"Error: Failed to analyze Git diff. Status code: {response.status_code}, Message: {response.text}"}
                
        except Exception as e:
            return {"result": f"Error: {str(e)}"} 