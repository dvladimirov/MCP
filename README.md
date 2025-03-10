# MCP Server with OpenAI, Git, Filesystem, and Prometheus Integration

This repository contains a Model Control Plane (MCP) server implementation that supports OpenAI services, Git repository analysis, local filesystem operations, and Prometheus integration.

## Project Structure

```
MCP/
├── mcp/               # Core MCP library modules
├── scripts/           # Utility scripts and test tools
├── prometheus/        # Prometheus configuration
├── docker-compose.yml # Docker configuration
├── mcp_server.py      # Main server implementation
├── mcp_run            # Main runner script (shortcut)
└── README.md          # This file
```

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- OpenAI SDK
- GitPython
- Requests
- Docker and Docker Compose (for Prometheus features)

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

For Prometheus:
```bash
export PROMETHEUS_URL="http://localhost:9090"  # Default if not specified
```

## Running the Server

Start the MCP server:

```bash
python scripts/start_mcp_server.py
```

Or for more options:

```bash
python scripts/start_mcp_server.py --host 0.0.0.0 --port 8000 --debug
```

The server will be available at http://localhost:8000.

## Unified Testing Tool

We provide a unified testing script that gives you a user-friendly interface to all testing functionality:

```bash
./mcp_run
```

This interactive script provides:
- Filesystem tests
- Git integration tests
- Memory analysis tools
- Prometheus tests & memory stress
- MCP server management
- Environment setup

## Individual Tests

You can also run individual tests directly:

Test the OpenAI integration:
```bash
python scripts/test_mcp_client.py
```

Test the Git integration (provide a Git repository URL):
```bash
python scripts/test_git_integration.py https://github.com/username/repository
```

Test the Git diff functionality (analyze requirements compatibility):
```bash
python scripts/test_git_diff.py https://github.com/username/repository [commit-sha]
```

Test the filesystem functionality:
```bash
python scripts/test_filesystem.py
```

Test the langflow integration with MCP:
```bash
python scripts/test_langflow_integration.py [OPTIONAL_REPO_URL]
```

Test the Prometheus integration:
```bash
python scripts/test_prometheus.py [prometheus_url]
```

## Advanced Git Analysis

For more advanced Git repository analysis with AI recommendations:

```bash
python scripts/langflow_git_analyzer.py https://github.com/username/repository
```

You can also search for specific patterns in the repository:

```bash
python scripts/langflow_git_analyzer.py https://github.com/username/repository --search "def main"
```

Or analyze the last commit diff with AI insights:

```bash
python scripts/langflow_git_analyzer.py https://github.com/username/repository --diff
```

## Memory Analysis Tools

MCP includes several tools for memory monitoring and analysis:

```bash
# Basic memory diagnostics with AI analysis
python scripts/ai_memory_diagnostics.py

# Interactive memory dashboard
python scripts/mcp_memory_dashboard.py

# Memory alerting system
python scripts/mcp_memory_alerting.py
```

You can also simulate memory pressure for testing:

```bash
python scripts/simulate_memory_pressure.py --target 85 --duration 300
```

## Prometheus Integration

### Setup

1. Start the Prometheus stack using Docker Compose:

```bash
docker compose up -d
```

This will start:
- Prometheus server (accessible at http://localhost:9090)
- Node Exporter (for host metrics)
- cAdvisor (for container metrics)

2. For stress testing, you can start the memory stress container:

```bash
docker compose up -d --build memory-stress
```

Or use the container test script:
```bash
./scripts/container-memory-test.sh start
```

### Using Prometheus Client

The `MCPAIComponent` class includes Prometheus capabilities:

```python
from langflow import MCPAIComponent

# Initialize the client
mcp = MCPAIComponent(mcp_server_url="http://localhost:8000")

# Instant query (current metric values)
result = mcp.prometheus_query("up")

# Range query (metrics over time)
result = mcp.prometheus_query_range(
    query="rate(node_cpu_seconds_total{mode='system'}[1m])",
    start="2023-03-01T00:00:00Z",
    end="2023-03-01T01:00:00Z",
    step="15s"
)

# Get all labels
labels = mcp.prometheus_get_labels()

# Get label values
values = mcp.prometheus_get_label_values("job")

# Get targets
targets = mcp.prometheus_get_targets()

# Get alerts
alerts = mcp.prometheus_get_alerts()
```

### Useful PromQL Queries

- CPU Usage: `rate(node_cpu_seconds_total{mode!="idle"}[1m])`
- Memory Usage: `node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes`
- Disk Usage: `node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}`
- Container CPU Usage: `rate(container_cpu_usage_seconds_total[1m])`
- Container Memory Usage: `container_memory_usage_bytes`

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

### Prometheus Endpoints
- POST `/v1/models/prometheus/query` - Execute an instant query
- POST `/v1/models/prometheus/query_range` - Execute a range query
- POST `/v1/models/prometheus/series` - Get series data
- GET `/v1/models/prometheus/labels` - Get all available labels
- POST `/v1/models/prometheus/label_values` - Get values for a specific label
- GET `/v1/models/prometheus/targets` - Get all targets
- GET `/v1/models/prometheus/rules` - Get all rules
- GET `/v1/models/prometheus/alerts` - Get all alerts

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

## Troubleshooting

### Prometheus Issues
1. Verify Prometheus is running: `docker ps | grep prometheus`
2. Check you can access the Prometheus UI: http://localhost:9090
3. Verify the MCP server is running and accessible
4. Check the MCP server logs for errors
5. Try simple queries first to verify connectivity (e.g., `up` query)

### OpenAI Issues
1. Verify your API keys are set correctly
2. Check for rate limiting or quota issues
3. Verify you're using supported models for your API key

### Git Issues
1. Ensure the Git repository URL is accessible
2. Check for authentication issues if using private repositories
3. Ensure GitPython is installed correctly 