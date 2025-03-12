#!/usr/bin/env python3
import os
import sys
import json
import argparse
import tempfile
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Add the parent directory to Python path for proper imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from langflow import MCPAIComponent

def analyze_git_diff(repo_url: str, commit_sha: str, 
                   target_commit: str = 'HEAD', 
                   capture_output: bool = False) -> Dict[str, Any]:
    """
    Analyze the diff between two commits in a Git repository.
    
    Args:
        repo_url: URL of the Git repository to analyze
        commit_sha: Base commit SHA to compare from
        target_commit: Target commit to compare to (default: HEAD)
        capture_output: If True, capture and return the output instead of printing
        
    Returns:
        Dict containing diff analysis information if capture_output=True
    """
    results = {}
    
    # Helper to log results
    def log_result(key: str, value: Any):
        if capture_output:
            results[key] = value
        else:
            print(f"\n=== {key} ===")
            if isinstance(value, (dict, list)):
                print(json.dumps(value, indent=2))
            else:
                print(value)
    
    log_result("analysis_type", "git_diff")
    log_result("repository", repo_url)
    log_result("base_commit", commit_sha)
    log_result("target_commit", target_commit)
    log_result("timestamp", datetime.now().isoformat())
    
    # Validate the commit SHA
    try:
        is_valid = validate_commit_sha(repo_url, commit_sha)
        if not is_valid:
            log_result("error", f"Invalid commit SHA: {commit_sha}")
            
            if capture_output:
                return results
            return {"status": "error", "message": f"Invalid commit SHA: {commit_sha}"}
    except Exception as e:
        log_result("error", f"Error validating commit SHA: {str(e)}")
        
        if capture_output:
            return results
        return {"status": "error", "message": str(e)}
    
    # Get the diff between commits
    try:
        diff_text = get_diff_between_commits(repo_url, commit_sha, target_commit)
        
        # Extract basic statistics
        diff_stats = {
            "total_lines": len(diff_text.splitlines()),
            "files_changed": diff_text.count("diff --git"),
            "additions": diff_text.count("\n+") - diff_text.count("\n+++"),
            "deletions": diff_text.count("\n-") - diff_text.count("\n---"),
        }
        
        log_result("diff_stats", diff_stats)
        
        # Check for requirements.txt changes
        try:
            old_requirements = get_file_from_commit(repo_url, commit_sha, "requirements.txt")
            new_requirements = get_file_from_commit(repo_url, target_commit, "requirements.txt")
            
            if old_requirements is not None and new_requirements is not None:
                added, removed, changed = compare_requirements(new_requirements, old_requirements)
                
                req_changes = {
                    "added": added,
                    "removed": removed,
                    "changed": changed,
                }
                
                log_result("requirements_changes", req_changes)
        except Exception as e:
            log_result("requirements_analysis_error", str(e))
        
        # Try to get a more detailed diff analysis using MCPAIComponent
        try:
            mcp = MCPAIComponent(mcp_server_url="http://localhost:8000")
            
            # Check if the analyze_diff endpoint exists
            models = mcp.list_models()
            has_diff_analyzer = any(model.get('id') == 'git-diff-analyzer' for model in models)
            
            if has_diff_analyzer:
                api_result = mcp.analyze_diff(repo_url, commit_sha, target_commit)
                
                if api_result and isinstance(api_result, dict) and 'status' in api_result:
                    log_result("api_analysis", api_result)
        except Exception as e:
            log_result("api_analysis_error", str(e))
    
    except Exception as e:
        log_result("error", str(e))
    
    # Return results if in capture mode
    if capture_output:
        return results
    else:
        return {"status": "completed", "output": "printed to console"}

def compare_requirements(current_reqs: str, previous_reqs: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Compare two requirements.txt files and identify added, removed, and changed dependencies.
    
    Args:
        current_reqs: Content of the current requirements.txt file
        previous_reqs: Content of the previous requirements.txt file
        
    Returns:
        Tuple of (added, removed, changed) dependencies
    """
    
    def parse_requirements(content: str) -> Dict[str, str]:
        """Parse requirements.txt content into a dictionary of package name -> version."""
        if not content or content.strip() == "":
            return {}
            
        result = {}
        for line in content.splitlines():
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                continue
                
            # Handle different formats: pkg==version, pkg>=version, etc.
            parts = line.split('==')
            if len(parts) == 2:
                # Standard version pinning (pkg==1.0.0)
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = version
            elif '>=' in line:
                # Minimum version (pkg>=1.0.0)
                parts = line.split('>=')
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = f">={version}"
            elif '>' in line:
                # Greater than version (pkg>1.0.0)
                parts = line.split('>')
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = f">{version}"
            elif '<=' in line:
                # Maximum version (pkg<=1.0.0)
                parts = line.split('<=')
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = f"<={version}"
            elif '<' in line:
                # Less than version (pkg<1.0.0)
                parts = line.split('<')
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = f"<{version}"
            else:
                # Just package name or other format
                pkg_name = line.strip()
                result[pkg_name] = "any"
                
        return result
    
    current_pkgs = parse_requirements(current_reqs)
    previous_pkgs = parse_requirements(previous_reqs)
    
    # Find added packages
    added = [f"{pkg}=={version}" for pkg, version in current_pkgs.items() 
             if pkg not in previous_pkgs]
    
    # Find removed packages
    removed = [f"{pkg}=={version}" for pkg, version in previous_pkgs.items() 
               if pkg not in current_pkgs]
    
    # Find changed versions
    changed = [f"{pkg}: {previous_pkgs[pkg]} -> {current_pkgs[pkg]}" 
               for pkg in current_pkgs 
               if pkg in previous_pkgs and current_pkgs[pkg] != previous_pkgs[pkg]]
    
    return added, removed, changed

def get_file_from_commit(repo_url: str, commit_sha: str, file_path: str) -> Optional[str]:
    """
    Get the content of a file from a specific commit in a Git repository.
    
    Args:
        repo_url: URL of the Git repository
        commit_sha: Commit SHA to extract the file from
        file_path: Path to the file within the repository
        
    Returns:
        Content of the file or None if the file doesn't exist in that commit
    """
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Clone the repository (shallow clone to save time and space)
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            check=True,
            capture_output=True
        )
        
        # Check out the specific commit
        try:
            subprocess.run(
                ["git", "checkout", commit_sha],
                cwd=temp_dir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            # Try fetching the commit first
            subprocess.run(
                ["git", "fetch", "--depth", "1", "origin", commit_sha],
                cwd=temp_dir,
                check=True,
                capture_output=True
            )
            
            # Now try to check out again
            subprocess.run(
                ["git", "checkout", commit_sha],
                cwd=temp_dir,
                check=True,
                capture_output=True
            )
        
        # Check if the file exists
        file_full_path = os.path.join(temp_dir, file_path)
        if not os.path.isfile(file_full_path):
            return None
        
        # Read the file content
        with open(file_full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
        return content
    except Exception as e:
        print(f"Error getting file '{file_path}' from commit {commit_sha}: {e}")
        # Clean up on error
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass
        return None

def validate_commit_sha(repo_url: str, commit_sha: str) -> bool:
    """
    Validate if a commit SHA exists in a repository.
    
    Args:
        repo_url: URL of the Git repository
        commit_sha: Commit SHA to validate
        
    Returns:
        True if the commit SHA exists, False otherwise
    """
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Clone the repository (shallow clone to save time and space)
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            check=True,
            capture_output=True
        )
        
        # Try to show the commit details
        try:
            # First, try to fetch the specific commit
            subprocess.run(
                ["git", "fetch", "--depth", "1", "origin", commit_sha],
                cwd=temp_dir,
                check=True,
                capture_output=True
            )
            
            # Then, check if the commit exists
            result = subprocess.run(
                ["git", "cat-file", "-t", commit_sha],
                cwd=temp_dir,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Clean up
            import shutil
            shutil.rmtree(temp_dir)
            
            # If the command succeeded, and returned "commit", the SHA is valid
            return result.stdout.strip() == "commit"
        except subprocess.CalledProcessError:
            # Clean up on error
            import shutil
            shutil.rmtree(temp_dir)
            return False
    except Exception as e:
        print(f"Error validating commit SHA: {e}")
        # Clean up on error
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass
        return False

def get_diff_between_commits(repo_url: str, base_commit: str, target_commit: str = 'HEAD') -> str:
    """
    Get the diff between two commits in a Git repository.
    
    Args:
        repo_url: URL of the Git repository
        base_commit: Base commit SHA
        target_commit: Target commit SHA (default: HEAD)
        
    Returns:
        Diff text between the commits
    """
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Clone the repository
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            check=True,
            capture_output=True
        )
        
        # Try to fetch both commits
        subprocess.run(
            ["git", "fetch", "--depth", "1", "origin", base_commit],
            cwd=temp_dir,
            check=True,
            capture_output=True
        )
        
        if target_commit != 'HEAD':
            subprocess.run(
                ["git", "fetch", "--depth", "1", "origin", target_commit],
                cwd=temp_dir,
                check=True,
                capture_output=True
            )
        
        # Get the diff
        result = subprocess.run(
            ["git", "diff", base_commit, target_commit],
            cwd=temp_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
        return result.stdout
    except Exception as e:
        print(f"Error getting diff between commits: {e}")
        # Clean up on error
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass
        return f"Error: {str(e)}"

def test_git_diff(repo_url=None, compare_commit=None):
    """
    Test git diff functionality between two commits.
    
    Args:
        repo_url: URL of the Git repository
        compare_commit: Base commit SHA to compare against
    """
    # Get repo URL from command line if not provided
    if not repo_url and len(sys.argv) > 1:
        repo_url = sys.argv[1]
        
    # Get commit SHA from command line if not provided
    if not compare_commit and len(sys.argv) > 2:
        compare_commit = sys.argv[2]
    
    # Check if we have the necessary information
    if not repo_url:
        print("Error: Please provide a Git repository URL")
        print("Usage: python test_git_diff.py <git-repo-url> [<commit-sha>]")
        sys.exit(1)
    
    print(f"Testing Git diff for repository: {repo_url}")
    
    if compare_commit:
        print(f"Comparing against commit: {compare_commit}")
        
        # Validate the commit SHA
        print(f"Validating commit SHA: {compare_commit}")
        is_valid = validate_commit_sha(repo_url, compare_commit)
        
        if is_valid:
            print(f"Commit SHA {compare_commit} is valid.")
            
            # Get the diff
            print(f"Getting diff between {compare_commit} and HEAD...")
            diff = get_diff_between_commits(repo_url, compare_commit)
            
            # Show basic statistics
            diff_lines = diff.splitlines()
            files_changed = diff.count("diff --git")
            additions = diff.count("\n+") - diff.count("\n+++")
            deletions = diff.count("\n-") - diff.count("\n---")
            
            print(f"\nDiff Statistics:")
            print(f"Files changed: {files_changed}")
            print(f"Additions: {additions}")
            print(f"Deletions: {deletions}")
            print(f"Total diff lines: {len(diff_lines)}")
            
            # Check for requirements.txt changes
            print("\nChecking for requirements.txt changes...")
            old_requirements = get_file_from_commit(repo_url, compare_commit, "requirements.txt")
            
            if old_requirements is not None:
                print("Found requirements.txt in the base commit.")
                
                # Get current requirements.txt
                new_requirements = get_file_from_commit(repo_url, "HEAD", "requirements.txt")
                
                if new_requirements is not None:
                    print("Found requirements.txt in the current commit.")
                    
                    # Compare requirements
                    added, removed, changed = compare_requirements(new_requirements, old_requirements)
                    
                    if added or removed or changed:
                        print("\nRequirements Changes:")
                        
                        if added:
                            print("\nAdded Dependencies:")
                            for dep in added:
                                print(f"  + {dep}")
                        
                        if removed:
                            print("\nRemoved Dependencies:")
                            for dep in removed:
                                print(f"  - {dep}")
                        
                        if changed:
                            print("\nChanged Dependencies:")
                            for dep in changed:
                                print(f"  ~ {dep}")
                    else:
                        print("No changes to requirements.txt dependencies.")
                else:
                    print("requirements.txt not found in the current commit.")
            else:
                print("requirements.txt not found in the base commit.")
            
            # Try to send the diff to the MCP server for AI analysis
            try:
                print("\nSending diff to MCP server for AI analysis...")
                mcp = MCPAIComponent(mcp_server_url="http://localhost:8000")
                
                # Check if the analyze_diff endpoint exists
                models = mcp.list_models()
                has_diff_analyzer = any(model.get('id') == 'git-diff-analyzer' for model in models)
                
                if has_diff_analyzer:
                    print("Found git-diff-analyzer model, sending request...")
                    result = mcp.analyze_diff(repo_url, compare_commit)
                    
                    if result and isinstance(result, dict) and 'summary' in result:
                        print("\nAI Analysis Summary:")
                        print(result['summary'])
                        
                        if 'major_changes' in result:
                            print("\nMajor Changes:")
                            for change in result['major_changes']:
                                print(f"  - {change}")
                        
                        if 'recommendations' in result:
                            print("\nRecommendations:")
                            for rec in result['recommendations']:
                                print(f"  - {rec}")
                    else:
                        print("No summary provided in the AI analysis result.")
                else:
                    print("git-diff-analyzer model not found on MCP server.")
            except Exception as e:
                print(f"Error during AI analysis: {e}")
        else:
            print(f"Error: Commit SHA {compare_commit} is invalid.")
    else:
        print("No commit SHA provided for comparison.")
        print("Showing the latest commit information instead.")
        
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Clone the repository
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, temp_dir],
                check=True,
                capture_output=True
            )
            
            # Get latest commit info
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%h|%an|%ad|%s"],
                cwd=temp_dir,
                check=True,
                capture_output=True,
                text=True
            )
            
            commit_parts = result.stdout.split('|')
            if len(commit_parts) >= 4:
                print("\nLatest Commit:")
                print(f"SHA: {commit_parts[0]}")
                print(f"Author: {commit_parts[1]}")
                print(f"Date: {commit_parts[2]}")
                print(f"Message: {commit_parts[3]}")
                print("\nUse this commit SHA to compare with an earlier version.")
            
            # Clean up
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error getting latest commit info: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Git diff functionality between commits")
    parser.add_argument("repo_url", nargs="?", help="URL of the Git repository")
    parser.add_argument("commit_sha", nargs="?", help="Base commit SHA to compare against")
    
    args = parser.parse_args()
    
    test_git_diff(args.repo_url, args.commit_sha) 