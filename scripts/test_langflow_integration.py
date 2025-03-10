import os
import json
from langflow import MCPAIComponent

def test_langflow_integration(repo_url=None):
    """Test the langflow integration with the MCP server."""
    
    print("Initializing MCPAIComponent...")
    mcp = MCPAIComponent(mcp_server_url="http://localhost:8000")
    
    # List available models
    print("\nAvailable models:")
    models = mcp.list_models()
    for model in models:
        capabilities = ', '.join(model.get('capabilities', []))
        print(f"- {model.get('id')}: {model.get('name')} (Capabilities: {capabilities})")
    
    # Test chat functionality with OpenAI
    print("\nTesting chat functionality with OpenAI model...")
    try:
        chat_response = mcp.chat(
            model_id="openai-gpt-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant with expertise in programming."},
                {"role": "user", "content": "Explain the concept of Model Control Plane (MCP) in 2-3 sentences."}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        # Extract and print the assistant's response
        choices = chat_response.get('choices', [])
        if choices:
            message = choices[0].get('message', {})
            content = message.get('content', '')
            print(f"Assistant's response: {content}")
        else:
            print("No response content received.")
    except Exception as e:
        print(f"Error testing chat functionality: {e}")
    
    # If a repository URL was provided, analyze it and use the results in a chat
    if repo_url:
        print(f"\nAnalyzing Git repository: {repo_url}")
        try:
            # Analyze the repository
            repo_analysis = mcp.analyze_git_repo(repo_url)
            
            # Print some basic repository information
            print(f"Repository URL: {repo_analysis.get('url')}")
            print(f"Active branch: {repo_analysis.get('active_branch')}")
            print(f"Total files: {repo_analysis.get('file_count')}")
            
            # Get file statistics
            file_stats = repo_analysis.get('file_stats', {})
            print(f"Python files: {file_stats.get('python_files', 0)}")
            print(f"JavaScript files: {file_stats.get('javascript_files', 0)}")
            print(f"HTML files: {file_stats.get('html_files', 0)}")
            
            # Use the repository analysis in a chat with the AI
            print("\nAsking AI about the analyzed repository...")
            
            # Prepare a summary of the repository for the AI
            repo_summary = (
                f"Repository: {repo_analysis.get('url')}\n"
                f"Branch: {repo_analysis.get('active_branch')}\n"
                f"Files: {repo_analysis.get('file_count')} total, "
                f"{file_stats.get('python_files', 0)} Python files, "
                f"{file_stats.get('javascript_files', 0)} JavaScript files, "
                f"{file_stats.get('html_files', 0)} HTML files\n"
                f"Last commit: {repo_analysis.get('last_commit', {}).get('message', '')}"
            )
            
            chat_response = mcp.chat(
                model_id="openai-gpt-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful programming assistant with expertise in code repositories."},
                    {"role": "user", "content": f"I've analyzed this repository. Based on the information below, what kind of project do you think this is and what technologies might it use?\n\n{repo_summary}"}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            # Extract and print the assistant's response
            choices = chat_response.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                content = message.get('content', '')
                print(f"Assistant's analysis: {content}")
            else:
                print("No response content received.")
                
        except Exception as e:
            print(f"Error analyzing repository: {e}")
    
    print("\nLangflow integration test complete!")

if __name__ == "__main__":
    import sys
    
    repo_url = None
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
    
    test_langflow_integration(repo_url) 