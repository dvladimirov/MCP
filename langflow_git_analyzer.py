import os
import json
import argparse
from langflow import MCPAIComponent
from typing import Dict, List, Any, Optional, Union

class GitCodeAnalyzer:
    """Class for analyzing and understanding code repositories using LLMs"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000"):
        """Initialize with MCP server URL"""
        self.mcp = MCPAIComponent(mcp_server_url=mcp_server_url)
        self.repo_data = None
        self.repo_url = None
    
    def analyze_repository(self, repo_url: str) -> Dict[str, Any]:
        """Analyze a Git repository and store the results
        
        Args:
            repo_url: URL of the Git repository to analyze
            
        Returns:
            Dict[str, Any]: Repository analysis results
        """
        self.repo_url = repo_url
        self.repo_data = self.mcp.analyze_git_repo(repo_url)
        return self.repo_data
    
    def search_repository(self, pattern: str) -> Dict[str, Any]:
        """Search the repository for files matching a pattern
        
        Args:
            pattern: Content pattern to search for
            
        Returns:
            Dict[str, Any]: Search results
        """
        if not self.repo_url:
            raise ValueError("No repository has been analyzed yet. Call analyze_repository first.")
        
        return self.mcp.search_git_repo(self.repo_url, pattern)
    
    def get_last_commit_diff(self) -> Dict[str, Any]:
        """Get the diff of the last commit in the repository
        
        Returns:
            Dict[str, Any]: Diff information
        """
        if not self.repo_url:
            raise ValueError("No repository has been analyzed yet. Call analyze_repository first.")
        
        return self.mcp.get_git_diff(self.repo_url)
    
    def get_formatted_diff_summary(self) -> str:
        """Get a formatted summary of the last commit diff
        
        Returns:
            str: Formatted diff summary
        """
        diff_info = self.get_last_commit_diff()
        
        if "error" in diff_info:
            return f"Error getting diff: {diff_info['error']}"
        
        commit_id = diff_info.get("commit_id", "")
        commit_message = diff_info.get("commit_message", "")
        commit_author = diff_info.get("commit_author", "")
        commit_date = diff_info.get("commit_date", "")
        total_files_changed = diff_info.get("total_files_changed", 0)
        total_additions = diff_info.get("total_additions", 0)
        total_deletions = diff_info.get("total_deletions", 0)
        
        summary = [
            f"Last Commit: {commit_id[:8]}",
            f"Author: {commit_author}",
            f"Date: {commit_date}",
            f"Message: {commit_message}",
            f"Changes: {total_files_changed} files changed, {total_additions} insertions(+), {total_deletions} deletions(-)",
            "\nChanged Files:"
        ]
        
        files_changed = diff_info.get("files_changed", [])
        for file_info in files_changed:
            path = file_info.get("path", "")
            change_type = file_info.get("change_type", "")
            additions = file_info.get("additions", 0)
            deletions = file_info.get("deletions", 0)
            
            summary.append(f"  {path} ({change_type}): +{additions} -{deletions}")
        
        return "\n".join(summary)
    
    def analyze_commit_diff(self) -> str:
        """Use AI to analyze the last commit diff
        
        Returns:
            str: AI analysis of the commit changes
        """
        diff_info = self.get_last_commit_diff()
        
        if "error" in diff_info:
            return f"Error getting diff: {diff_info['error']}"
        
        # Create a summary of the diff for the AI
        commit_message = diff_info.get("commit_message", "")
        total_files_changed = diff_info.get("total_files_changed", 0)
        total_additions = diff_info.get("total_additions", 0)
        total_deletions = diff_info.get("total_deletions", 0)
        
        files_summary = []
        files_changed = diff_info.get("files_changed", [])
        
        # Limit to 3 files for the prompt to avoid token limits
        for file_info in files_changed[:3]:
            path = file_info.get("path", "")
            change_type = file_info.get("change_type", "")
            additions = file_info.get("additions", 0)
            deletions = file_info.get("deletions", 0)
            diff = file_info.get("diff", "")
            
            # Truncate large diffs
            diff_preview = diff[:1000] + "..." if len(diff) > 1000 else diff
            
            files_summary.append(
                f"File: {path}\n"
                f"Change Type: {change_type}\n"
                f"Changes: +{additions} -{deletions}\n"
                f"Diff Preview:\n{diff_preview}\n"
            )
        
        # Create the prompt
        diff_summary = (
            f"Commit Message: {commit_message}\n"
            f"Total Changes: {total_files_changed} files changed, {total_additions} insertions(+), {total_deletions} deletions(-)\n\n"
            f"File Changes (showing up to 3 files):\n"
            f"{''.join(files_summary)}"
        )
        
        if len(files_changed) > 3:
            diff_summary += f"\n... and {len(files_changed) - 3} more files not shown"
        
        # Ask AI to analyze the changes
        chat_response = self.mcp.chat(
            model_id="openai-gpt-chat",
            messages=[
                {"role": "system", "content": "You are an expert code reviewer and developer. Your task is to analyze git commit diffs and provide insights about the changes."},
                {"role": "user", "content": f"Please analyze this commit and provide:\n1. A summary of what changed\n2. The purpose of these changes\n3. Potential impact on the codebase\n4. Any potential issues or improvements\n\nHere's the diff information:\n\n{diff_summary}"}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract the assistant's response
        choices = chat_response.get('choices', [])
        if choices:
            message = choices[0].get('message', {})
            content = message.get('content', '')
            return content
        else:
            return "Unable to analyze the commit diff."
    
    def get_repository_summary(self) -> str:
        """Generate a summary of the repository
        
        Returns:
            str: Repository summary text
        """
        if not self.repo_data:
            raise ValueError("No repository has been analyzed yet. Call analyze_repository first.")
        
        file_stats = self.repo_data.get('file_stats', {})
        last_commit = self.repo_data.get('last_commit', {})
        
        summary = (
            f"Repository URL: {self.repo_data.get('url')}\n"
            f"Active Branch: {self.repo_data.get('active_branch')}\n"
            f"Total Files: {self.repo_data.get('file_count')}\n"
            f"File Types:\n"
            f"  - Python: {file_stats.get('python_files', 0)}\n"
            f"  - JavaScript: {file_stats.get('javascript_files', 0)}\n"
            f"  - HTML: {file_stats.get('html_files', 0)}\n"
            f"Last Commit:\n"
            f"  - Author: {last_commit.get('author')}\n"
            f"  - Message: {last_commit.get('message')}\n"
            f"  - Date: {last_commit.get('date')}\n"
        )
        
        return summary
    
    def get_repository_recommendations(self) -> str:
        """Use AI to provide recommendations about the repository
        
        Returns:
            str: AI-generated recommendations
        """
        if not self.repo_data:
            raise ValueError("No repository has been analyzed yet. Call analyze_repository first.")
        
        summary = self.get_repository_summary()
        
        chat_response = self.mcp.chat(
            model_id="openai-gpt-chat",
            messages=[
                {"role": "system", "content": "You are an expert code repository analyzer. Your task is to analyze repository metadata and provide useful insights and recommendations."},
                {"role": "user", "content": f"Please analyze this repository and provide:\n1. What type of project this likely is\n2. Key technologies used\n3. Three specific recommendations for improving this codebase\n\nRepository details:\n{summary}"}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract the assistant's response
        choices = chat_response.get('choices', [])
        if choices:
            message = choices[0].get('message', {})
            content = message.get('content', '')
            return content
        else:
            return "Unable to generate recommendations."
    
    def analyze_code_pattern(self, pattern: str) -> str:
        """Search for a pattern and have AI analyze the matching files
        
        Args:
            pattern: Content pattern to search for
            
        Returns:
            str: AI analysis of the matching files
        """
        search_results = self.search_repository(pattern)
        matching_files = search_results.get('matching_files', [])
        match_count = search_results.get('match_count', 0)
        
        if match_count == 0:
            return f"No files matching the pattern '{pattern}' were found."
        
        # Only include up to 5 files in the prompt to avoid token limits
        files_to_include = matching_files[:5]
        files_summary = "\n".join([f"- {file}" for file in files_to_include])
        if len(matching_files) > 5:
            files_summary += f"\n- ...and {len(matching_files) - 5} more files"
        
        chat_response = self.mcp.chat(
            model_id="openai-gpt-chat",
            messages=[
                {"role": "system", "content": "You are an expert code analyst. Your task is to analyze code patterns and provide insights."},
                {"role": "user", "content": f"I searched for the pattern '{pattern}' in my repository and found {match_count} files containing this pattern. Here are some of the matching files:\n\n{files_summary}\n\nBased on this information, what might this pattern represent in the codebase? What functionality might these files implement? Provide a brief analysis."}
            ],
            max_tokens=350,
            temperature=0.7
        )
        
        # Extract the assistant's response
        choices = chat_response.get('choices', [])
        if choices:
            message = choices[0].get('message', {})
            content = message.get('content', '')
            return content
        else:
            return "Unable to analyze the code pattern."

def main():
    parser = argparse.ArgumentParser(description="Analyze Git repositories with AI")
    parser.add_argument("repo_url", help="URL of the Git repository to analyze")
    parser.add_argument("--search", "-s", help="Search for a specific pattern in the repository")
    parser.add_argument("--diff", "-d", action="store_true", help="Get and analyze the last commit diff")
    parser.add_argument("--mcp-url", default="http://localhost:8000", help="URL of the MCP server")
    args = parser.parse_args()
    
    analyzer = GitCodeAnalyzer(mcp_server_url=args.mcp_url)
    
    print(f"Analyzing repository: {args.repo_url}")
    analyzer.analyze_repository(args.repo_url)
    
    if args.diff:
        print("\nLast Commit Diff Summary:")
        print(analyzer.get_formatted_diff_summary())
        
        print("\nAI Analysis of Commit:")
        analysis = analyzer.analyze_commit_diff()
        print(analysis)
    else:
        print("\nRepository Summary:")
        print(analyzer.get_repository_summary())
        
        print("\nAI Recommendations:")
        recommendations = analyzer.get_repository_recommendations()
        print(recommendations)
    
    if args.search:
        print(f"\nAnalyzing code pattern: '{args.search}'")
        pattern_analysis = analyzer.analyze_code_pattern(args.search)
        print(pattern_analysis)

if __name__ == "__main__":
    main() 