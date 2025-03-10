#!/usr/bin/env python3
import os
import sys

# Add the parent directory to Python path for proper imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import json
import requests
from typing import Dict, List, Any, Optional, Callable

# Define our own simple component decorator instead of importing from langflow
def component(cls):
    """Simple component decorator for compatibility"""
    return cls

@component
class MCPAIComponent:
    """Component for interacting with MCP-compliant AI services"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000"):
        self.mcp_server_url = mcp_server_url
        self.available_models = self._fetch_available_models()
        
    def _fetch_available_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from the MCP server"""
        try:
            response = requests.get(f"{self.mcp_server_url}/v1/models")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            print(f"Error fetching models from MCP server: {e}")
            return []
    
    def list_models(self) -> List[Dict[str, Any]]:
        """Return list of available models"""
        return self.available_models
    
    def completion(self, 
                   model_id: str, 
                   prompt: str, 
                   max_tokens: int = 100, 
                   temperature: float = 0.7) -> Dict[str, Any]:
        """Generate a text completion using the specified model"""
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/{model_id}/completion",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def chat(self, 
             model_id: str, 
             messages: List[Dict[str, str]], 
             max_tokens: int = 100, 
             temperature: float = 0.7) -> Dict[str, Any]:
        """Generate a chat response using the specified model"""
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/{model_id}/chat",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_git_repo(self, repo_url: str) -> Dict[str, Any]:
        """Analyze a Git repository
        
        Args:
            repo_url: URL of the Git repository to analyze
            
        Returns:
            Dict[str, Any]: Repository analysis results
        """
        payload = {
            "repo_url": repo_url
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/git-analyzer/analyze",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def search_git_repo(self, repo_url: str, pattern: str) -> Dict[str, Any]:
        """Search a Git repository for files matching a pattern
        
        Args:
            repo_url: URL of the Git repository to search
            pattern: Content pattern to search for
            
        Returns:
            Dict[str, Any]: Search results
        """
        payload = {
            "repo_url": repo_url,
            "pattern": pattern
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/git-analyzer/search",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_git_diff(self, repo_url: str) -> Dict[str, Any]:
        """Get the diff of the last commit in a Git repository
        
        Args:
            repo_url: URL of the Git repository
            
        Returns:
            Dict[str, Any]: Diff information of the last commit
        """
        payload = {
            "repo_url": repo_url
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/git-analyzer/diff",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List contents of a directory
        
        Args:
            path: Path of the directory to list (default: current directory)
            
        Returns:
            Dict[str, Any]: Directory listing
        """
        payload = {
            "path": path
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/filesystem/list",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """Read the contents of a file
        
        Args:
            path: Path of the file to read
            
        Returns:
            Dict[str, Any]: File content and path
        """
        payload = {
            "path": path
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/filesystem/read",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def read_multiple_files(self, paths: List[str]) -> Dict[str, Any]:
        """Read multiple files at once
        
        Args:
            paths: List of file paths to read
            
        Returns:
            Dict[str, Any]: Dictionary with file contents and error info
        """
        payload = {
            "paths": paths
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/filesystem/read-multiple",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file
        
        Args:
            path: Path of the file to write
            content: Content to write to the file
            
        Returns:
            Dict[str, Any]: Result information
        """
        payload = {
            "path": path,
            "content": content
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/filesystem/write",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def edit_file(self, path: str, edits: List[Dict[str, str]], dry_run: bool = False) -> Dict[str, Any]:
        """Edit a file with multiple replacements
        
        Args:
            path: Path of the file to edit
            edits: List of edits to apply. Each edit has 'oldText' and 'newText'
            dry_run: Whether to simulate the edit without making changes
            
        Returns:
            Dict[str, Any]: Result of the operation including diff information
        """
        payload = {
            "path": path,
            "edits": edits,
            "dry_run": dry_run
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/filesystem/edit",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory
        
        Args:
            path: Path of the directory to create
            
        Returns:
            Dict[str, Any]: Result information
        """
        payload = {
            "path": path
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/filesystem/mkdir",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move a file or directory
        
        Args:
            source: Source path
            destination: Destination path
            
        Returns:
            Dict[str, Any]: Result information
        """
        payload = {
            "source": source,
            "destination": destination
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/filesystem/move",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def search_files(self, pattern: str, path: str = ".", exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """Search for files matching a pattern
        
        Args:
            pattern: Search pattern (glob format)
            path: Directory to search in (default: current directory)
            exclude_patterns: Patterns to exclude
            
        Returns:
            Dict[str, Any]: Search results
        """
        payload = {
            "path": path,
            "pattern": pattern
        }
        
        if exclude_patterns:
            payload["exclude_patterns"] = exclude_patterns
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/filesystem/search",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get information about a file or directory
        
        Args:
            path: Path to the file or directory
            
        Returns:
            Dict[str, Any]: File information
        """
        payload = {
            "path": path
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/filesystem/info",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    # Prometheus methods
    def prometheus_query(self, query: str, time: Optional[str] = None) -> Dict[str, Any]:
        """Execute an instant query against Prometheus
        
        Args:
            query: PromQL query expression
            time: Evaluation timestamp (rfc3339 or unix_timestamp), optional
            
        Returns:
            Dict[str, Any]: Query result
        """
        payload = {
            "query": query
        }
        
        if time:
            payload["time"] = time
            
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/prometheus/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def prometheus_query_range(self, query: str, start: str, end: str, step: str) -> Dict[str, Any]:
        """Execute a range query against Prometheus
        
        Args:
            query: PromQL query expression
            start: Start timestamp (rfc3339 or unix_timestamp)
            end: End timestamp (rfc3339 or unix_timestamp)
            step: Query resolution step width
            
        Returns:
            Dict[str, Any]: Range query result
        """
        payload = {
            "query": query,
            "start": start,
            "end": end,
            "step": step
        }
            
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/prometheus/query_range",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def prometheus_get_series(
        self, 
        match: List[str], 
        start: Optional[str] = None, 
        end: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find series matching a label set
        
        Args:
            match: Series selector string array
            start: Start timestamp, optional
            end: End timestamp, optional
            
        Returns:
            Dict[str, Any]: Series data
        """
        payload = {
            "match": match
        }
        
        if start:
            payload["start"] = start
        if end:
            payload["end"] = end
            
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/prometheus/series",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def prometheus_get_labels(self) -> Dict[str, Any]:
        """Get all label names
        
        Returns:
            Dict[str, Any]: Label names
        """
        response = requests.get(
            f"{self.mcp_server_url}/v1/models/prometheus/labels"
        )
        response.raise_for_status()
        return response.json()
    
    def prometheus_get_label_values(self, label_name: str) -> Dict[str, Any]:
        """Get values for a label
        
        Args:
            label_name: Label name
            
        Returns:
            Dict[str, Any]: Label values
        """
        payload = {
            "label_name": label_name
        }
        
        response = requests.post(
            f"{self.mcp_server_url}/v1/models/prometheus/label_values",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def prometheus_get_targets(self) -> Dict[str, Any]:
        """Get targets
        
        Returns:
            Dict[str, Any]: Targets information
        """
        response = requests.get(
            f"{self.mcp_server_url}/v1/models/prometheus/targets"
        )
        response.raise_for_status()
        return response.json()
    
    def prometheus_get_rules(self) -> Dict[str, Any]:
        """Get rules
        
        Returns:
            Dict[str, Any]: Rules information
        """
        response = requests.get(
            f"{self.mcp_server_url}/v1/models/prometheus/rules"
        )
        response.raise_for_status()
        return response.json()
    
    def prometheus_get_alerts(self) -> Dict[str, Any]:
        """Get alerts
        
        Returns:
            Dict[str, Any]: Alerts information
        """
        response = requests.get(
            f"{self.mcp_server_url}/v1/models/prometheus/alerts"
        )
        response.raise_for_status()
        return response.json()
    
    def process(self, 
                input_type: str = "chat",  # "chat" or "completion"
                model_id: str = "azure-gpt-4", 
                prompt: Optional[str] = None,
                messages: Optional[List[Dict[str, str]]] = None,
                max_tokens: int = 100,
                temperature: float = 0.7) -> Dict[str, Any]:
        """Process input through the MCP server"""
        
        if input_type == "chat" and messages:
            return self.chat(model_id, messages, max_tokens, temperature)
        elif input_type == "completion" and prompt:
            return self.completion(model_id, prompt, max_tokens, temperature)
        else:
            raise ValueError("Invalid input configuration. For chat, provide 'messages'. For completion, provide 'prompt'.")