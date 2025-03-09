# MCP Server with OpenAI, Git, and Filesystem Integration

This repository contains a Model Control Plane (MCP) server implementation that supports OpenAI services, Git repository analysis, and local filesystem operations.

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- OpenAI SDK
- GitPython
- Requests

## Installation

1. Clone this repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Set the following environment variables:

For Azure OpenAI:
```bash
export AZURE_OPENAI_ENDPOINT="your-azure-endpoint"
export AZURE_OPENAI_API_KEY="your-azure-api-key"
export AZURE_OPENAI_API_VERSION="2023-05-15"
export AZURE_DEPLOYMENT_NAME="your-deployment-name"
```

For Standard OpenAI:
```bash
export OPENAI_API_KEY="your-openai-api-key"
# Optional: Specify which models to use
export OPENAI_CHAT_MODEL="gpt-4o-mini"  # Default if not specified
export OPENAI_COMPLETION_MODEL="gpt-3.5-turbo-instruct"  # Default if not specified
```

## Running the Server

Start the MCP server:

```bash
python mcp_server.py
```

The server will be available at http://localhost:8000.

## Testing

Test the OpenAI integration:
```bash
python test_mcp_client.py
```

Test the Git integration (provide a Git repository URL):
```bash
python test_git_integration.py https://github.com/username/repository
```

Test the Git diff functionality (analyze the last commit):
```bash
python test_git_diff.py https://github.com/username/repository
```

Test the filesystem functionality:
```bash
python test_filesystem.py
```

Test the langflow integration with MCP:
```bash
python test_langflow_integration.py [OPTIONAL_REPO_URL]
```

## Advanced Git Analysis

For more advanced Git repository analysis with AI recommendations:

```bash
python langflow_git_analyzer.py https://github.com/username/repository
```

You can also search for specific patterns in the repository:

```bash
python langflow_git_analyzer.py https://github.com/username/repository --search "def main"
```

Or analyze the last commit diff with AI insights:

```bash
python langflow_git_analyzer.py https://github.com/username/repository --diff
```

## API Endpoints

### OpenAI Endpoints
- GET `/v1/models` - List all available models
- GET `/v1/models/{model_id}` - Get information about a specific model
- POST `/v1/models/azure-gpt-4/completion` - Generate text completion using Azure OpenAI
- POST `/v1/models/azure-gpt-4/chat` - Generate chat response using Azure OpenAI
- POST `/v1/models/openai-gpt-chat/chat` - Generate chat response using OpenAI chat model
- POST `/v1/models/openai-gpt-completion/completion` - Generate text completion using OpenAI completion model

### Git Integration Endpoints
- POST `/v1/models/git-analyzer/analyze` - Analyze a Git repository
- POST `/v1/models/git-analyzer/search` - Search a Git repository for files matching a pattern
- POST `/v1/models/git-analyzer/diff` - Get the diff of the last commit in a repository

### Filesystem Endpoints
- POST `/v1/models/filesystem/list` - List contents of a directory
- POST `/v1/models/filesystem/read` - Read a file's contents
- POST `/v1/models/filesystem/read-multiple` - Read multiple files at once
- POST `/v1/models/filesystem/write` - Write content to a file
- POST `/v1/models/filesystem/edit` - Edit a file with multiple replacements
- POST `/v1/models/filesystem/mkdir` - Create a directory
- POST `/v1/models/filesystem/move` - Move a file or directory
- POST `/v1/models/filesystem/search` - Search for files matching a pattern
- POST `/v1/models/filesystem/info` - Get information about a file or directory

## Client Usage

You can use the `MCPAIComponent` in your LangFlow pipelines by providing the MCP server URL:

```python
from langflow import MCPAIComponent

mcp = MCPAIComponent(mcp_server_url="http://localhost:8000")

# List available models
models = mcp.list_models()
print(models)

# Generate chat completion with OpenAI model
chat_response = mcp.chat(
    model_id="openai-gpt-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a joke about programming."}
    ],
    max_tokens=100,
    temperature=0.7
)
print(chat_response)

# Generate text completion with OpenAI model
completion_response = mcp.completion(
    model_id="openai-gpt-completion",
    prompt="Write a function in Python to calculate the factorial of a number:",
    max_tokens=150,
    temperature=0.7
)
print(completion_response)

# Analyze a Git repository
repo_analysis = mcp.analyze_git_repo("https://github.com/username/repository")
print(repo_analysis)

# Search a Git repository
search_results = mcp.search_git_repo("https://github.com/username/repository", "def main")
print(search_results)

# Get the diff of the last commit
diff_info = mcp.get_git_diff("https://github.com/username/repository")
print(diff_info)

# List files in the current directory
dir_contents = mcp.list_directory()
print(dir_contents)

# Read a file
file_content = mcp.read_file("path/to/file.txt")
print(file_content)

# Write to a file
write_result = mcp.write_file("path/to/new_file.txt", "Hello, world!")
print(write_result)

# Search for files
search_result = mcp.search_files("*.py")
print(search_result)
```

## Using the GitCodeAnalyzer Class

For more structured Git analysis, you can use the `GitCodeAnalyzer` class:

```python
from langflow_git_analyzer import GitCodeAnalyzer

# Initialize the analyzer
analyzer = GitCodeAnalyzer(mcp_server_url="http://localhost:8000")

# Analyze a repository
analyzer.analyze_repository("https://github.com/username/repository")

# Get a summary
summary = analyzer.get_repository_summary()
print(summary)

# Get AI recommendations
recommendations = analyzer.get_repository_recommendations()
print(recommendations)

# Analyze code patterns
pattern_analysis = analyzer.analyze_code_pattern("def process")
print(pattern_analysis)

# Get the last commit diff
diff_info = analyzer.get_last_commit_diff()
print(diff_info)

# Get a formatted summary of the diff
diff_summary = analyzer.get_formatted_diff_summary()
print(diff_summary)

# Get AI analysis of the commit changes
diff_analysis = analyzer.analyze_commit_diff()
print(diff_analysis)
``` 