#!/usr/bin/env python3
"""
MCP Feature Showcase

This script demonstrates the key features of the MCP (Mission Control Platform),
making it easy to test and showcase functionality through langflow.

Current demonstrations:
- Filesystem operations
- Git repository analysis

Usage:
  python showcase_mcp_features.py --feature filesystem
  python showcase_mcp_features.py --feature git --repo-url https://github.com/username/repo
  
Reports are generated and can be viewed in Langflow (http://localhost:7860)
"""

import os
import sys
import json
import argparse
import tempfile
import http.server
import socketserver
import threading
import webbrowser
import signal
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the parent directory to Python path for proper imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import MCP-specific modules
from langflow import MCPAIComponent
import scripts.test_filesystem as filesystem_module
import scripts.test_git_integration as git_module
import scripts.test_git_diff as git_diff_module

# Define the reports directory
REPORTS_DIR = os.path.join(parent_dir, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Global variable to track if we should keep running
keep_running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C by setting the keep_running flag to False."""
    global keep_running
    print("\nShutting down server. Please wait...")
    keep_running = False
    sys.exit(0)

# Set up signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

def generate_html_report(title: str, results: Dict[str, Any], feature_type: str) -> str:
    """Generate an HTML report from the showcase results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{feature_type}_showcase_{timestamp}.html"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    
    # Start building the HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .card {{
            background-color: #f9f9f9;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }}
        .success {{
            color: #27ae60;
            font-weight: bold;
        }}
        .error {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-style: italic;
        }}
        pre {{
            background-color: #f1f1f1;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .highlight {{
            background-color: #e8f4fc;
        }}
        .ai-analysis {{
            background-color: #f0f8ff;
            border-left: 4px solid #3498db;
            padding: 10px 20px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p class="timestamp">Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
"""

    # Add content based on feature type
    if feature_type == "filesystem":
        html_content += generate_filesystem_report_content(results)
    elif feature_type == "git":
        html_content += generate_git_report_content(results)
    
    # Add link back to Langflow
    html_content += """
    <div class="card">
        <h3>Return to Langflow</h3>
        <p><a href="http://localhost:7860" target="_blank">Go back to Langflow UI</a></p>
    </div>
"""
    
    # Close the HTML document
    html_content += """
</body>
</html>
"""
    
    # Write the HTML content to the file
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return report_path

def generate_filesystem_report_content(results: Dict[str, Any]) -> str:
    """Generate the HTML content for filesystem analysis."""
    content = """
    <div class="card">
        <h2>Filesystem Analysis Summary</h2>
"""
    
    # Add summary statistics
    content += f"""
        <p><strong>Total Files:</strong> {len(results.get('files', []))}</p>
        <p><strong>Total Directories:</strong> {len(results.get('directories', []))}</p>
        <p><strong>Total Size:</strong> {results.get('total_size_bytes', 0) / (1024 * 1024):.2f} MB</p>
    </div>
"""
    
    # Add file type distribution
    content += """
    <div class="card">
        <h2>File Type Distribution</h2>
        <table>
            <tr>
                <th>Extension</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""
    
    file_types = results.get('file_types', {})
    total_files = sum(file_types.values())
    
    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:20]:
        percentage = (count / total_files * 100) if total_files > 0 else 0
        content += f"""
            <tr>
                <td>{ext}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""
    
    content += """
        </table>
    </div>
"""
    
    # Add largest files
    content += """
    <div class="card">
        <h2>Largest Files</h2>
        <table>
            <tr>
                <th>Path</th>
                <th>Size (MB)</th>
                <th>Modified</th>
            </tr>
"""
    
    for file_info in results.get('largest_files', [])[:10]:
        size_mb = file_info.get('size_bytes', 0) / (1024 * 1024)
        modified = file_info.get('modified', 'Unknown')
        path = file_info.get('path', 'Unknown')
        
        content += f"""
            <tr>
                <td>{path}</td>
                <td>{size_mb:.2f} MB</td>
                <td>{modified}</td>
            </tr>
"""
    
    content += """
        </table>
    </div>
"""
    
    # Add AI analysis if available
    if 'ai_analysis' in results:
        content += """
    <div class="card ai-analysis">
        <h2>AI-Generated Analysis</h2>
"""
        # Replace newlines with <br> tags for proper HTML rendering
        ai_analysis = results.get('ai_analysis', 'No AI analysis available').replace('\n', '<br>')
        content += f"<p>{ai_analysis}</p>"
        content += """
    </div>
"""
    
    return content

def generate_git_report_content(results: Dict[str, Any]) -> str:
    """Generate the HTML content for git repository analysis."""
    repo_url = results.get('repository', 'Unknown')
    
    content = f"""
    <div class="card">
        <h2>Git Repository Analysis</h2>
        <p><strong>Repository:</strong> {repo_url}</p>
        <p><strong>Analysis Time:</strong> {results.get('timestamp', 'Unknown')}</p>
    </div>
"""
    
    # Add repository statistics
    repo_stats = results.get('repository_stats', {})
    if repo_stats:
        content += """
    <div class="card">
        <h2>Repository Statistics</h2>
"""
        for key, value in repo_stats.items():
            # Convert key from snake_case to Title Case for display
            display_key = ' '.join(word.capitalize() for word in key.split('_'))
            content += f"<p><strong>{display_key}:</strong> {value}</p>"
        
        content += """
    </div>
"""
    
    # Add file type breakdown
    file_types = results.get('file_types', {})
    if file_types:
        content += """
    <div class="card">
        <h2>File Type Distribution</h2>
        <table>
            <tr>
                <th>Extension</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""
        
        total_files = sum(file_types.values())
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:15]:
            percentage = (count / total_files * 100) if total_files > 0 else 0
            content += f"""
            <tr>
                <td>{ext}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""
        
        content += """
        </table>
    </div>
"""
    
    # Add recent commits
    commit_history = results.get('recent_commits', [])
    if commit_history:
        content += """
    <div class="card">
        <h2>Recent Commits</h2>
        <table>
            <tr>
                <th>SHA</th>
                <th>Author</th>
                <th>Date</th>
                <th>Message</th>
            </tr>
"""
        
        for commit in commit_history[:10]:
            sha = commit.get('sha', 'Unknown')[:7]  # First 7 chars of SHA
            author = commit.get('author', 'Unknown')
            date = commit.get('date', 'Unknown')
            message = commit.get('message', 'No message')
            
            content += f"""
            <tr>
                <td>{sha}</td>
                <td>{author}</td>
                <td>{date}</td>
                <td>{message}</td>
            </tr>
"""
        
        content += """
        </table>
    </div>
"""
    
    # Add diff analysis if available
    diff_analysis = results.get('diff_analysis', {})
    if diff_analysis:
        content += """
    <div class="card">
        <h2>Diff Analysis</h2>
"""
        diff_stats = diff_analysis.get('diff_stats', {})
        if diff_stats:
            content += "<h3>Change Statistics</h3>"
            content += "<ul>"
            content += f"<li><strong>Files Changed:</strong> {diff_stats.get('files_changed', 0)}</li>"
            content += f"<li><strong>Additions:</strong> {diff_stats.get('additions', 0)}</li>"
            content += f"<li><strong>Deletions:</strong> {diff_stats.get('deletions', 0)}</li>"
            content += f"<li><strong>Total Lines:</strong> {diff_stats.get('total_lines', 0)}</li>"
            content += "</ul>"
        
        # Add requirements changes if available
        req_changes = diff_analysis.get('requirements_changes', {})
        if req_changes:
            content += "<h3>Requirements.txt Changes</h3>"
            
            if req_changes.get('added'):
                content += "<h4>Added Dependencies</h4>"
                content += "<ul>"
                for dep in req_changes.get('added', []):
                    content += f"<li>{dep}</li>"
                content += "</ul>"
            
            if req_changes.get('removed'):
                content += "<h4>Removed Dependencies</h4>"
                content += "<ul>"
                for dep in req_changes.get('removed', []):
                    content += f"<li>{dep}</li>"
                content += "</ul>"
            
            if req_changes.get('changed'):
                content += "<h4>Changed Dependencies</h4>"
                content += "<ul>"
                for dep in req_changes.get('changed', []):
                    content += f"<li>{dep}</li>"
                content += "</ul>"
        
        content += """
    </div>
"""
    
    # Add AI analysis if available
    if 'ai_analysis' in results:
        content += """
    <div class="card ai-analysis">
        <h2>AI-Generated Repository Analysis</h2>
"""
        # Replace newlines with <br> tags for proper HTML rendering
        ai_analysis = results.get('ai_analysis', 'No AI analysis available').replace('\n', '<br>')
        content += f"<p>{ai_analysis}</p>"
        content += """
    </div>
"""
    
    return content

class ReportHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=REPORTS_DIR, **kwargs)
    
    def log_message(self, format, *args):
        # Silence the HTTP server logs
        pass

def serve_reports(port=8765):
    """Start a simple HTTP server to serve the reports."""
    try:
        with socketserver.TCPServer(("", port), ReportHTTPHandler) as httpd:
            print(f"Report server started at http://localhost:{port}")
            global keep_running
            while keep_running:
                httpd.handle_request()
    except OSError:
        # If the port is in use, try another one
        if port < 8775:
            serve_reports(port + 1)
        else:
            print("Could not start report server - all ports in range are busy")

def start_report_server():
    """Start the report server in a background thread."""
    server_thread = threading.Thread(target=serve_reports)
    server_thread.daemon = True
    server_thread.start()
    return server_thread

def showcase_filesystem() -> Dict[str, Any]:
    """Showcase filesystem operations and analysis."""
    print("=== Showcasing Filesystem Operations ===")
    
    # Use the capture_output parameter to get results instead of printing
    results = filesystem_module.analyze_filesystem(capture_output=True)
    
    # Print a summary of the results
    print(f"\nAnalyzed {len(results.get('files', []))} files across {len(results.get('directories', []))} directories")
    print(f"Found {len(results.get('file_types', {}))} different file types")
    
    # Extract and display the top file types by count
    file_types = results.get('file_types', {})
    sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
    
    print("\nTop file types by count:")
    for file_type, count in sorted_types[:5]:
        print(f"  - {file_type}: {count} files")
    
    # Show largest files
    largest_files = results.get('largest_files', [])
    if largest_files:
        print("\nLargest files in the workspace:")
        for file_info in largest_files[:3]:
            size_mb = file_info.get('size_bytes', 0) / (1024 * 1024)
            print(f"  - {file_info.get('path')}: {size_mb:.2f} MB")
    
    # Generate AI analysis if available
    if 'ai_analysis' in results:
        print("\n=== AI-Generated Filesystem Analysis ===")
        print(results.get('ai_analysis', 'No AI analysis available'))
    
    # Generate HTML report
    report_path = generate_html_report(
        title="MCP Filesystem Analysis Report", 
        results=results,
        feature_type="filesystem"
    )
    
    # Get the relative path to display
    rel_report_path = os.path.relpath(report_path, parent_dir)
    
    # Add report path to results
    results['report_path'] = report_path
    results['report_url'] = f"http://localhost:8765/{os.path.basename(report_path)}"
    
    print(f"\n✅ Report generated: {rel_report_path}")
    print(f"📊 View in browser: {results['report_url']}")
    print("   (You can view this URL in the Langflow interface)")
    
    return results

def normalize_repo_url(repo_url: str) -> str:
    """Normalize the repository URL to ensure compatibility."""
    if not repo_url:
        return repo_url
        
    # Remove trailing slashes
    repo_url = repo_url.rstrip('/')
    
    # Ensure .git extension for GitHub URLs
    if 'github.com' in repo_url and not repo_url.endswith('.git'):
        return f"{repo_url}.git"
    
    return repo_url

def analyze_git_repo(repo_url, commit_sha=None):
    """
    Analyze a Git repository and generate a report with key insights.
    
    Args:
        repo_url: URL of the Git repository to analyze
        commit_sha: Optional specific commit SHA to analyze
        
    Returns:
        Dict containing analysis results
    """
    print(f"\n🔍 Analyzing Git repository: {repo_url}")
    if commit_sha:
        print(f"📋 Focusing on commit: {commit_sha}")
    
    # Get main repository analysis using the git integration module
    results = git_module.analyze_repo(repo_url, capture_output=True)
    
    # If a specific commit is provided, do a diff analysis on it
    if commit_sha:
        print(f"\n📊 Analyzing commit diff for: {commit_sha}")
        try:
            diff_results = git_diff_module.analyze_git_diff(
                repo_url=repo_url,
                commit_sha=commit_sha,
                capture_output=True
            )
            
            # Merge the diff results with the main results
            if diff_results:
                results['diff_analysis'] = diff_results
                
                # Extract key metrics for display
                if 'diff_stats' in diff_results:
                    print("\n=== Diff Analysis ===")
                    stats = diff_results['diff_stats']
                    print(f"Files changed: {stats.get('files_changed', 'Unknown')}")
                    print(f"Additions: {stats.get('additions', 'Unknown')}")
                    print(f"Deletions: {stats.get('deletions', 'Unknown')}")
                
                if 'requirements_changes' in diff_results:
                    changes = diff_results['requirements_changes']
                    if any(changes.values()):
                        print("\n=== Requirements Changes ===")
                        if changes.get('added'):
                            print(f"Added: {', '.join(changes['added'])}")
                        if changes.get('removed'):
                            print(f"Removed: {', '.join(changes['removed'])}")
                        if changes.get('changed'):
                            print(f"Changed: {', '.join(changes['changed'])}")
        except Exception as e:
            print(f"Error in diff analysis: {str(e)}")
    
    # Try to perform a Git diff analysis on the most recent commit if no specific commit was provided
    if not commit_sha:
        try:
            # Get most recent commit if we have one
            recent_commit = None
            commit_history = results.get('commit_history', [])
            
            if 'latest_commit_sha' in results:
                recent_commit = results['latest_commit_sha']
            elif commit_history and len(commit_history) > 0:
                recent_commit = commit_history[0].get('hash')
                
            # If we have a recent commit SHA and at least two commits, try to analyze the diff
            if recent_commit and len(commit_history) > 1:
                print(f"\n=== Analyzing diff for most recent commit {recent_commit[:7]} ===")
                
                # Get the parent commit
                parent_commit = commit_history[1].get('hash')
                
                if parent_commit:
                    try:
                        # Use the analyze_git_diff function to get proper diff analysis
                        diff_results = git_diff_module.analyze_git_diff(
                            repo_url=repo_url,
                            commit_sha=parent_commit,
                            target_commit=recent_commit,
                            capture_output=True
                        )
                        
                        if diff_results:
                            results['diff_analysis'] = diff_results
                            
                            # Extract key metrics for display
                            if 'diff_stats' in diff_results:
                                print("\n=== Diff Analysis ===")
                                stats = diff_results['diff_stats']
                                print(f"Files changed: {stats.get('files_changed', 'Unknown')}")
                                print(f"Additions: {stats.get('additions', 'Unknown')}")
                                print(f"Deletions: {stats.get('deletions', 'Unknown')}")
                    except Exception as e:
                        print(f"Error analyzing commit diff: {str(e)}")
                    
            else:
                # Fallback to single commit analysis
                if recent_commit:
                    print(f"\n=== Analyzing repository at commit {recent_commit[:7]} ===")
                    
                    repo_info = {
                        "repository": repo_url,
                        "commit_sha": recent_commit,
                        "single_commit": True
                    }
                    
                    results['single_commit_analysis'] = repo_info
                    print(f"  - Repository: {repo_url}")
                    print(f"  - Commit: {recent_commit[:7]}")
        except Exception as e:
            print(f"Error retrieving commit information: {str(e)}")
    
    # Generate HTML report
    report_path = generate_html_report(
        title=f"MCP Git Analysis Report - {os.path.basename(repo_url)}",
        results=results,
        feature_type="git"
    )
    
    # Get the relative path to display
    rel_report_path = os.path.relpath(report_path, parent_dir)
    
    # Add report path to results
    results['report_path'] = report_path
    results['report_url'] = f"http://localhost:8765/{os.path.basename(report_path)}"
    
    print(f"\n✅ Report generated: {rel_report_path}")
    print(f"📊 View in browser: {results['report_url']}")
    print("   (You can view this URL in the Langflow interface)")
    
    return results

def showcase_git(repo_url: str) -> Dict[str, Any]:
    """Showcase Git repository analysis."""
    if not repo_url:
        print("Error: Repository URL is required for Git showcase.")
        print("Usage: python showcase_mcp_features.py --feature git --repo-url https://github.com/username/repo")
        return {"error": "Repository URL is required"}
    
    # Normalize the repository URL to ensure consistent format
    repo_url = normalize_repo_url(repo_url)
    
    print(f"=== Showcasing Git Analysis for {repo_url} ===")
    print("Please wait, cloning repository and analyzing data...")
    
    # Call the analyze_git_repo function to perform the analysis
    return analyze_git_repo(repo_url)

def wait_for_user_exit():
    """Keep the server running until the user presses Ctrl+C."""
    global keep_running
    try:
        print("\nServer is running. Press Ctrl+C to exit.")
        while keep_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        keep_running = False

def main():
    parser = argparse.ArgumentParser(description="MCP Feature Showcase Tool")
    parser.add_argument("--feature", choices=["filesystem", "git"], required=True,
                      help="Feature to showcase (filesystem or git)")
    parser.add_argument("--repo-url", help="Git repository URL (required for git feature)")
    parser.add_argument("--commit-sha", help="Optional: Specific Git commit SHA to analyze")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--open-browser", action="store_true", help="Open the report in a browser automatically")
    parser.add_argument("--exit-when-done", action="store_true", help="Exit after generating the report (default: keep running)")
    
    args = parser.parse_args()
    
    # Start the report server in a background thread
    server_thread = start_report_server()
    print("🌐 Started report server at http://localhost:8765")
    
    # Call the appropriate showcase function based on the selected feature
    results = {}
    
    if args.feature == "filesystem":
        results = showcase_filesystem()
    elif args.feature == "git":
        repo_url = args.repo_url
        if not repo_url:
            parser.error("--repo-url is required for git feature")
        
        # Validate and normalize Git repository URL
        repo_url = normalize_repo_url(repo_url)
        
        # Run the Git showcase with optional commit_sha
        if args.commit_sha:
            print(f"Analyzing specific commit: {args.commit_sha}")
            results = analyze_git_repo(repo_url, args.commit_sha)
        else:
            results = showcase_git(repo_url)
    
    # Output as JSON if requested
    if args.json:
        print("\n=== JSON Output ===")
        # We exclude the large file and directory lists to keep the output manageable
        output_results = {k: v for k, v in results.items() if k not in ['files', 'directories']}
        print(json.dumps(output_results, indent=2))
    
    # Open the report in the browser if requested
    if args.open_browser and 'report_url' in results:
        print("\nOpening report in browser...")
        webbrowser.open(results['report_url'])
    
    # Display tips for viewing in Langflow
    print("\n💡 Tips for viewing in Langflow:")
    print("1. Copy the report URL shown above")
    print("2. In Langflow, create a custom component that displays the URL in an iframe")
    print("3. Or use a 'Text' component to share the URL with users")
    
    print("\n📋 Full report URL for copying into Langflow:")
    if 'report_url' in results:
        print(results['report_url'])
    
    # Keep the server running unless explicitly told to exit
    if not args.exit_when_done:
        print("\n⚠️ Keep this terminal running to view the report.")
        print("The report server will continue running until you press Ctrl+C.")
        wait_for_user_exit()
    else:
        print("\nExiting as requested with --exit-when-done flag.")

if __name__ == "__main__":
    main() 