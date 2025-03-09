#!/usr/bin/env python3
import sys
import json
from langflow import MCPAIComponent

def test_git_diff(repo_url=None):
    """Test the git diff functionality."""
    
    if not repo_url:
        print("Error: Please provide a Git repository URL")
        print("Usage: python test_git_diff.py <git-repo-url>")
        sys.exit(1)
    
    print(f"Analyzing diff for repository: {repo_url}")
    
    # Initialize the MCP component
    mcp = MCPAIComponent(mcp_server_url="http://localhost:8000")
    
    try:
        # Get the diff of the last commit
        diff_info = mcp.get_git_diff(repo_url)
        
        # Extract basic commit info
        commit_id = diff_info.get('commit_id', 'N/A')
        commit_message = diff_info.get('commit_message', 'N/A')
        commit_author = diff_info.get('commit_author', 'N/A')
        commit_date = diff_info.get('commit_date', 'N/A')
        
        print("\nLast Commit Info:")
        print(f"Commit ID: {commit_id}")
        print(f"Author: {commit_author}")
        print(f"Date: {commit_date}")
        print(f"Message: {commit_message}")
        
        # Print statistics
        total_files = diff_info.get('total_files_changed', 0)
        total_additions = diff_info.get('total_additions', 0)
        total_deletions = diff_info.get('total_deletions', 0)
        
        print(f"\nChanges: {total_files} files changed, {total_additions} insertions(+), {total_deletions} deletions(-)")
        
        # Print file changes
        files_changed = diff_info.get('files_changed', [])
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
        
        # Use AI to analyze the commit
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
    repo_url = None
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
    
    test_git_diff(repo_url) 