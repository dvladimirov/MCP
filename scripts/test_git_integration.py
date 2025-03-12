import os
import requests
import json
from typing import Dict, Any, Optional, List, Union
import sys
import tempfile
import subprocess
from datetime import datetime

def analyze_repo(repo_url: str, base_url: str = "http://localhost:8000", capture_output: bool = False) -> Dict[str, Any]:
    """
    Analyze a Git repository and return useful information about it.
    
    Args:
        repo_url: URL of the Git repository to analyze
        base_url: URL of the MCP server
        capture_output: If True, capture and return the output instead of printing
        
    Returns:
        Dict containing repository analysis information
    """
    results = {}
    
    # Helper function to log or print results
    def log_result(key: str, value: Any):
        if capture_output:
            results[key] = value
        else:
            print(f"\n=== {key} ===")
            if isinstance(value, (dict, list)):
                print(json.dumps(value, indent=2))
            else:
                print(value)
    
    # Clone repo to temporary directory
    try:
        temp_dir = tempfile.mkdtemp(prefix="mcp_git_analysis_")
        log_result("temporary_directory", temp_dir)
        
        # Clone the repository
        clone_start = datetime.now()
        log_result("cloning_repo", f"Cloning {repo_url} into {temp_dir}")
        
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], 
                      check=True, capture_output=True)
        
        clone_duration = (datetime.now() - clone_start).total_seconds()
        log_result("clone_duration_seconds", clone_duration)
        
        # Get basic repository info
        repo_info = {}
        
        # Get commit count (approximate with depth=1)
        try:
            commit_count_cmd = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=temp_dir,
                check=True,
                capture_output=True,
                text=True
            )
            repo_info["commit_count"] = int(commit_count_cmd.stdout.strip())
        except (subprocess.SubprocessError, ValueError):
            repo_info["commit_count"] = "unknown"
        
        # Get last commit info
        try:
            last_commit_cmd = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%h|%an|%ad|%s"],
                cwd=temp_dir,
                check=True,
                capture_output=True,
                text=True
            )
            commit_parts = last_commit_cmd.stdout.split("|")
            repo_info["last_commit"] = {
                "hash": commit_parts[0],
                "author": commit_parts[1],
                "date": commit_parts[2],
                "message": commit_parts[3] if len(commit_parts) > 3 else ""
            }
        except subprocess.SubprocessError:
            repo_info["last_commit"] = "unknown"
        
        # Get file types and count
        file_types = {}
        try:
            for root, _, files in os.walk(temp_dir):
                if ".git" in root:
                    continue
                    
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1
                    else:
                        file_types["no_extension"] = file_types.get("no_extension", 0) + 1
            
            # Sort by count
            file_types = {k: v for k, v in sorted(file_types.items(), 
                                                 key=lambda item: item[1], reverse=True)}
            repo_info["file_types"] = file_types
            repo_info["file_count"] = sum(file_types.values())
            
            # Determine primary language
            lang_map = {
                ".py": "Python",
                ".js": "JavaScript",
                ".ts": "TypeScript",
                ".java": "Java",
                ".c": "C",
                ".cpp": "C++",
                ".cs": "C#",
                ".go": "Go",
                ".rs": "Rust",
                ".rb": "Ruby",
                ".php": "PHP",
                ".html": "HTML",
                ".css": "CSS",
                ".sh": "Shell",
                ".md": "Markdown"
            }
            
            # Find the most common extension that maps to a language
            primary_lang = "Unknown"
            for ext, count in file_types.items():
                if ext in lang_map:
                    primary_lang = lang_map[ext]
                    break
            
            repo_info["primary_language"] = primary_lang
            
        except Exception as e:
            repo_info["file_count"] = "error"
            repo_info["error"] = str(e)
        
        log_result("repository_info", repo_info)
        
        # Also try server-side analysis if the MCP server is available
        try:
            # Test repository analysis through MCP API
            analyze_payload = {"repo_url": repo_url}
            response = requests.post(f"{base_url}/v1/git/analyze", json=analyze_payload)
            
            if response.status_code == 200:
                server_analysis = response.json()
                log_result("server_analysis", server_analysis)
            else:
                log_result("server_analysis_error", 
                          f"Error: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            log_result("server_connection_error", str(e))
        
        # Clean up
        try:
            import shutil
            shutil.rmtree(temp_dir)
            log_result("cleanup", "Removed temporary directory")
        except Exception as e:
            log_result("cleanup_error", str(e))
    
    except Exception as e:
        log_result("error", str(e))
    
    # Return the collected results if in capture mode
    if capture_output:
        return results
    else:
        return {"status": "completed", "output": "printed to console"}

def test_git_integration(base_url: str = "http://localhost:8000", repo_url: str = None):
    """Test the Git integration in the MCP server"""
    
    if not repo_url:
        # If no repo_url is provided as an argument, check if it was passed from CLI
        if len(sys.argv) > 1:
            repo_url = sys.argv[1]
        else:
            print("Error: Please provide a Git repository URL")
            print("Usage: python test_git_integration.py <git-repo-url>")
            sys.exit(1)
    
    print(f"Testing Git integration with repository: {repo_url}")
    print(f"MCP server: {base_url}")
    
    # Run the repository analysis
    analyze_repo(repo_url, base_url, capture_output=False)
    
    print("\nGit integration test completed.")

if __name__ == "__main__":
    test_git_integration() 