import os
import requests
import json
from typing import Dict, Any
import sys

def test_git_integration(base_url: str = "http://localhost:8000", repo_url: str = None):
    """Test the Git integration in the MCP server"""
    
    if not repo_url:
        print("Error: Please provide a Git repository URL")
        print("Usage: python test_git_integration.py <git-repo-url>")
        sys.exit(1)
    
    # Test repository analysis
    print(f"Analyzing repository: {repo_url}")
    analyze_payload = {
        "repo_url": repo_url
    }
    
    analyze_response = requests.post(
        f"{base_url}/v1/models/git-analyzer/analyze",
        json=analyze_payload
    )
    
    if analyze_response.status_code == 200:
        result = analyze_response.json()
        print(f"\nRepository Analysis Results:")
        print(f"URL: {result.get('url')}")
        print(f"Active Branch: {result.get('active_branch')}")
        
        last_commit = result.get('last_commit', {})
        print(f"\nLast Commit:")
        print(f"  ID: {last_commit.get('id')}")
        print(f"  Author: {last_commit.get('author')}")
        print(f"  Message: {last_commit.get('message')}")
        print(f"  Date: {last_commit.get('date')}")
        
        file_stats = result.get('file_stats', {})
        print(f"\nFile Statistics:")
        print(f"  Total Files: {result.get('file_count')}")
        print(f"  Python Files: {file_stats.get('python_files')}")
        print(f"  JavaScript Files: {file_stats.get('javascript_files')}")
        print(f"  HTML Files: {file_stats.get('html_files')}")
        
        # Show a preview of the directory structure
        print("\nDirectory Structure Preview:")
        structure = result.get('directory_structure', {})
        for name, content in list(structure.items())[:5]:  # Show first 5 entries
            print(f"  {name}: {'<directory>' if isinstance(content, dict) else '<file>'}")
        
        if len(structure) > 5:
            print(f"  ... and {len(structure) - 5} more top-level items")
    else:
        print(f"Error analyzing repository: {analyze_response.status_code}")
        print(analyze_response.text)
    
    # Test repository search
    search_term = "def "  # Search for Python function definitions
    print(f"\nSearching repository for: '{search_term}'")
    search_payload = {
        "repo_url": repo_url,
        "pattern": search_term
    }
    
    search_response = requests.post(
        f"{base_url}/v1/models/git-analyzer/search",
        json=search_payload
    )
    
    if search_response.status_code == 200:
        result = search_response.json()
        matching_files = result.get('matching_files', [])
        
        print(f"Found {result.get('match_count')} files containing '{search_term}':")
        for i, file in enumerate(matching_files[:10]):  # Show first 10 matches
            print(f"  {i+1}. {file}")
        
        if len(matching_files) > 10:
            print(f"  ... and {len(matching_files) - 10} more files")
    else:
        print(f"Error searching repository: {search_response.status_code}")
        print(search_response.text)

if __name__ == "__main__":
    repo_url = None
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
    
    test_git_integration(repo_url=repo_url) 