#!/usr/bin/env python3
import os
import sys
import json
import argparse
import tempfile
import subprocess
from typing import Dict, List, Optional, Any, Tuple

# Add the parent directory to Python path for proper imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from langflow import MCPAIComponent

def compare_requirements(current_reqs: str, previous_reqs: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Compare two requirements.txt files and identify added, removed, and changed dependencies.
    
    Args:
        current_reqs: Content of the current requirements.txt
        previous_reqs: Content of the previous requirements.txt
        
    Returns:
        Tuple of (added, removed, changed) dependencies
    """
    def parse_requirements(content: str) -> Dict[str, str]:
        """Parse requirements into a dictionary of {package: version}"""
        result = {}
        for line in content.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Handle various formats like package==1.0.0, package>=1.0.0, etc.
            if '==' in line:
                package, version = line.split('==', 1)
                result[package.strip()] = version.strip()
            elif '>=' in line:
                package, version = line.split('>=', 1)
                result[package.strip()] = f">={version.strip()}"
            elif '<=' in line:
                package, version = line.split('<=', 1)
                result[package.strip()] = f"<={version.strip()}"
            elif '>' in line:
                package, version = line.split('>', 1)
                result[package.strip()] = f">{version.strip()}"
            elif '<' in line:
                package, version = line.split('<', 1)
                result[package.strip()] = f"<{version.strip()}"
            else:
                # Handle packages without version specifications
                result[line.strip()] = "any"
                
        return result
    
    current_dict = parse_requirements(current_reqs)
    previous_dict = parse_requirements(previous_reqs)
    
    # Find added, removed, and changed dependencies
    added = []
    for pkg in current_dict:
        if pkg not in previous_dict:
            added.append(f"{pkg}=={current_dict[pkg]}")
    
    removed = []
    for pkg in previous_dict:
        if pkg not in current_dict:
            removed.append(f"{pkg}=={previous_dict[pkg]}")
    
    changed = []
    for pkg in current_dict:
        if pkg in previous_dict and current_dict[pkg] != previous_dict[pkg]:
            changed.append(f"{pkg}: {previous_dict[pkg]} -> {current_dict[pkg]}")
            
    return added, removed, changed

def get_file_from_commit(repo_url: str, commit_sha: str, file_path: str) -> Optional[str]:
    """
    Get the content of a file from a specific commit in a Git repository.
    
    Args:
        repo_url: URL of the Git repository
        commit_sha: Commit SHA to get the file from
        file_path: Path to the file within the repository
        
    Returns:
        Content of the file or None if the file doesn't exist
    """
    print(f"Retrieving {file_path} from commit {commit_sha} in repository {repo_url}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone the repository without the commit SHA
            print(f"Cloning repository {repo_url}...")
            clone_cmd = ["git", "clone", repo_url, temp_dir]
            
            result = subprocess.run(clone_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error cloning repository: {result.stderr}")
                return None
            
            # Try to get the file content directly from git show
            try:
                print(f"Getting file content at commit {commit_sha}...")
                show_cmd = ["git", "show", f"{commit_sha}:{file_path}"]
                show_result = subprocess.run(show_cmd, cwd=temp_dir, capture_output=True, text=True)
                
                if show_result.returncode == 0:
                    return show_result.stdout
                
                print(f"File not found using git show, trying checkout method...")
                
                # If git show fails, try to checkout the commit and read the file
                checkout_cmd = ["git", "checkout", commit_sha]
                checkout_result = subprocess.run(checkout_cmd, cwd=temp_dir, capture_output=True, text=True)
                
                if checkout_result.returncode != 0:
                    print(f"Error checking out commit: {checkout_result.stderr}")
                    return None
                
                # Read the file directly from the filesystem
                file_fullpath = os.path.join(temp_dir, file_path)
                if os.path.exists(file_fullpath):
                    with open(file_fullpath, 'r') as f:
                        file_content = f.read()
                    print(f"File {file_path} found and read successfully")
                    return file_content
                else:
                    print(f"File {file_path} not found in commit {commit_sha}")
                    # List files in the repo root to help debug
                    print("Listing files in repository root:")
                    ls_cmd = ["ls", "-la"]
                    ls_result = subprocess.run(ls_cmd, cwd=temp_dir, capture_output=True, text=True)
                    if ls_result.returncode == 0:
                        print(ls_result.stdout)
                    return None
                
            except subprocess.CalledProcessError as e:
                print(f"Error accessing file in commit: {e}")
                return None
        except Exception as e:
            print(f"Error accessing repository: {e}")
            return None

def validate_commit_sha(repo_url: str, commit_sha: str) -> bool:
    """
    Validate if a commit SHA exists in the repository.
    
    Args:
        repo_url: URL of the Git repository
        commit_sha: SHA of the commit to validate
        
    Returns:
        True if the commit exists, False otherwise
    """
    print(f"Validating commit SHA: {commit_sha}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone the repository 
            print(f"Cloning repository for validation...")
            clone_cmd = ["git", "clone", "--bare", repo_url, temp_dir]
            
            result = subprocess.run(clone_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error cloning repository: {result.stderr}")
                return False
            
            # Check if commit exists
            check_cmd = ["git", "cat-file", "-e", commit_sha]
            check_result = subprocess.run(check_cmd, cwd=temp_dir, capture_output=True, text=True)
            
            if check_result.returncode == 0:
                print(f"Commit {commit_sha} exists in the repository")
                return True
            else:
                print(f"Commit {commit_sha} does not exist in the repository")
                return False
                
        except Exception as e:
            print(f"Error validating commit SHA: {e}")
            return False

def get_diff_between_commits(repo_url: str, base_commit: str, target_commit: str = 'HEAD') -> str:
    """
    Get the diff between two commits.
    
    Args:
        repo_url: URL of the Git repository
        base_commit: Base commit SHA
        target_commit: Target commit SHA (defaults to HEAD)
        
    Returns:
        Diff output as a string
    """
    print(f"Getting diff between {base_commit} and {target_commit}...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone the repository
            clone_cmd = ["git", "clone", repo_url, temp_dir]
            clone_result = subprocess.run(clone_cmd, capture_output=True, text=True)
            
            if clone_result.returncode != 0:
                print(f"Error cloning repository: {clone_result.stderr}")
                return "Error cloning repository"
            
            # Get the diff
            diff_cmd = ["git", "diff", base_commit, target_commit, "--", "requirements.txt"]
            diff_result = subprocess.run(diff_cmd, cwd=temp_dir, capture_output=True, text=True)
            
            if diff_result.returncode == 0:
                if diff_result.stdout:
                    return diff_result.stdout
                else:
                    return "No differences found in requirements.txt"
            else:
                print(f"Error getting diff: {diff_result.stderr}")
                return f"Error: {diff_result.stderr}"
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: {e}"

def test_git_diff(repo_url=None, compare_commit=None):
    """
    Test the git diff functionality with requirements.txt compatibility check.
    
    Args:
        repo_url: URL of the Git repository
        compare_commit: SHA of the commit to compare with the latest commit
    """
    
    if not repo_url:
        print("Error: Please provide a Git repository URL")
        print("Usage: python test_git_diff.py <git-repo-url> [commit-sha]")
        sys.exit(1)
    
    print(f"Analyzing repository: {repo_url}")
    
    # Validate commit SHA if provided
    if compare_commit:
        print(f"Comparing with commit: {compare_commit}")
        if not validate_commit_sha(repo_url, compare_commit):
            print(f"Invalid commit SHA: {compare_commit}")
            sys.exit(1)
    
    # Initialize the MCP component
    try:
        mcp = MCPAIComponent(mcp_server_url="http://localhost:8000")
    except Exception as e:
        print(f"Error initializing MCP component: {e}")
        sys.exit(1)
    
    try:
        # Get the diff of the last commit
        print("Fetching diff from the MCP server...")
        diff_info = mcp.get_git_diff(repo_url)
        
        # Extract basic commit info
        current_commit_id = diff_info.get('commit_id', 'N/A')
        commit_message = diff_info.get('commit_message', 'N/A')
        commit_author = diff_info.get('commit_author', 'N/A')
        commit_date = diff_info.get('commit_date', 'N/A')
        
        print("\nLatest Commit Info:")
        print(f"Commit ID: {current_commit_id}")
        print(f"Author: {commit_author}")
        print(f"Date: {commit_date}")
        print(f"Message: {commit_message}")
        
        # Print statistics
        total_files = diff_info.get('total_files_changed', 0)
        total_additions = diff_info.get('total_additions', 0)
        total_deletions = diff_info.get('total_deletions', 0)
        
        print(f"\nChanges: {total_files} files changed, {total_additions} insertions(+), {total_deletions} deletions(-)")
        
        # Get the current requirements.txt directly from the repository
        # We're not relying on the diff info which might be incomplete
        with tempfile.TemporaryDirectory() as temp_dir:
            print("\nDirectly retrieving current requirements.txt...")
            clone_cmd = ["git", "clone", repo_url, temp_dir]
            clone_result = subprocess.run(clone_cmd, capture_output=True, text=True)
            
            if clone_result.returncode != 0:
                print(f"Error cloning repository: {clone_result.stderr}")
                return
            
            requirements_path = os.path.join(temp_dir, 'requirements.txt')
            current_requirements = None
            if os.path.exists(requirements_path):
                with open(requirements_path, 'r') as f:
                    current_requirements = f.read()
                print("Found current requirements.txt")
            else:
                print("No requirements.txt found in the current commit")
                # List the root directory to help debug
                print("Listing repository root:")
                ls_cmd = ["ls", "-la"]
                ls_result = subprocess.run(ls_cmd, cwd=temp_dir, capture_output=True, text=True)
                if ls_result.returncode == 0:
                    print(ls_result.stdout)
        
        if compare_commit:
            print(f"\nComparing latest commit {current_commit_id[:7]} with {compare_commit[:7]}")
            
            # Get a direct diff between the commits for debugging purposes
            manual_diff = get_diff_between_commits(repo_url, compare_commit, current_commit_id)
            print("\nDirect git diff output for requirements.txt:")
            print(manual_diff)
            
            # Get requirements.txt from the specified commit
            previous_requirements = get_file_from_commit(repo_url, compare_commit, 'requirements.txt')
            
            if current_requirements is not None and previous_requirements is not None:
                print("\nAnalyzing requirements.txt compatibility...")
                added, removed, changed = compare_requirements(current_requirements, previous_requirements)
                
                if not (added or removed or changed):
                    print("No changes to requirements.txt between commits.")
                else:
                    if added:
                        print("\nAdded dependencies:")
                        for dep in added:
                            print(f"  + {dep}")
                    
                    if removed:
                        print("\nRemoved dependencies:")
                        for dep in removed:
                            print(f"  - {dep}")
                    
                    if changed:
                        print("\nChanged dependencies:")
                        for dep in changed:
                            print(f"  * {dep}")
                
                # Ask AI to analyze compatibility
                print("\nAsking AI to analyze requirements compatibility...")
                
                # Prepare the prompt
                prompt = f"""
                I need to analyze the compatibility between two versions of requirements.txt.
                
                Current requirements:
                ```
                {current_requirements}
                ```
                
                Previous requirements (from commit {compare_commit[:7]}):
                ```
                {previous_requirements}
                ```
                
                Changes summary:
                - Added: {', '.join(added) if added else 'None'}
                - Removed: {', '.join(removed) if removed else 'None'}
                - Changed: {', '.join(changed) if changed else 'None'}
                
                Raw diff:
                ```
                {manual_diff}
                ```
                
                Please analyze these changes and provide:
                1. Are these changes compatible with the existing codebase?
                2. Any potential dependency conflicts or issues?
                3. Security concerns with the changes (e.g., outdated versions, known vulnerabilities)?
                4. Recommendations for a safe upgrade path
                5. Should this change be approved for merging? (Yes/No/Need more information)
                """
                
                try:
                    chat_response = mcp.chat(
                        model_id="openai-gpt-chat",
                        messages=[
                            {"role": "system", "content": "You are an expert Python developer with deep knowledge of Python packaging, dependencies, and security. Your task is to analyze changes to requirements.txt files and provide compatibility assessments."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=800,
                        temperature=0.7
                    )
                    
                    choices = chat_response.get('choices', [])
                    if choices:
                        message = choices[0].get('message', {})
                        content = message.get('content', '')
                        print(f"\nAI Analysis:\n{content}")
                    else:
                        print("\nUnable to generate AI analysis.")
                except Exception as e:
                    print(f"\nError getting AI analysis: {e}")
            else:
                if current_requirements is None:
                    print("No requirements.txt found in the current commit.")
                if previous_requirements is None:
                    print(f"No requirements.txt found in commit {compare_commit[:7]}.")
        else:
            # If no comparison commit specified, show changes by file
            if files_changed:
                print("\nChanged Files:")
                for i, file_info in enumerate(files_changed, 1):
                    path = file_info.get('path', 'N/A')
                    change_type = file_info.get('change_type', 'N/A')
                    additions = file_info.get('additions', 0)
                    deletions = file_info.get('deletions', 0)
                    
                    print(f"{i}. {path} ({change_type}): +{additions} -{deletions}")
                    
                    # Ask if user wants to see the diff for this file
                    if i < len(files_changed):  # Don't ask for the last file
                        show_diff = input(f"\nShow diff for {path}? (y/n, default: n): ").lower() == 'y'
                        if show_diff:
                            diff = file_info.get('diff', 'No diff available')
                            print(f"\nDiff for {path}:\n{diff}\n")
                            input("Press Enter to continue...")
                    else:
                        # Always show the diff for the last file without asking
                        diff = file_info.get('diff', 'No diff available')
                        print(f"\nDiff for {path}:\n{diff}\n")
            else:
                print("\nNo files changed in the last commit.")
            
            # Allow the user to request generic AI analysis for any commit
            print("\nWould you like an AI analysis of this commit? (y/n, default: y): ", end="")
            analyze = input().lower() != 'n'
            
            if analyze:
                print("\nAsking AI to analyze the commit...")
                
                chat_response = mcp.chat(
                    model_id="openai-gpt-chat",
                    messages=[
                        {"role": "system", "content": "You are an expert code reviewer and developer. Your task is to analyze git commit diffs and provide insights about the changes."},
                        {"role": "user", "content": f"Please analyze this commit and provide:\n1. A summary of what changed\n2. The purpose of these changes\n3. Potential impact on the codebase\n4. Any potential issues or improvements\n\nHere's the information about the commit:\n\nCommit Message: {commit_message}\nTotal Changes: {total_files} files changed, {total_additions} insertions(+), {total_deletions} deletions(-)"}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                
                choices = chat_response.get('choices', [])
                if choices:
                    message = choices[0].get('message', {})
                    content = message.get('content', '')
                    print(f"\nAI Analysis:\n{content}")
                else:
                    print("\nUnable to generate AI analysis.")
    
    except Exception as e:
        print(f"Error analyzing diff: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test git diff functionality with requirements.txt compatibility check")
    parser.add_argument("repo_url", nargs="?", help="URL of the Git repository")
    parser.add_argument("commit_sha", nargs="?", help="SHA of the commit to compare with the latest commit")
    parser.add_argument("--help-more", action="store_true", help="Show more detailed help information")
    
    args = parser.parse_args()
    
    if args.help_more:
        print("Git Diff Analyzer with Requirements.txt Compatibility Check")
        print("=========================================================")
        print("\nThis tool analyzes a Git repository to compare requirements.txt files between commits.")
        print("It uses AI to assess compatibility, detect potential issues, and provide upgrade recommendations.")
        print("\nUsage:")
        print("  python test_git_diff.py <repository-url> [commit-sha]")
        print("\nExamples:")
        print("  python test_git_diff.py https://github.com/username/repo")
        print("    - Analyzes the latest commit in the repository")
        print("  python test_git_diff.py https://github.com/username/repo abc123")
        print("    - Compares the latest commit with commit 'abc123', focusing on requirements.txt")
        sys.exit(0)
    
    if not args.repo_url:
        parser.print_help()
        sys.exit(1)
        
    test_git_diff(args.repo_url, args.commit_sha) 