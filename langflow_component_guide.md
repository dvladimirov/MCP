# MCPComponent Guide for Langflow

This guide will help you understand how to use the MCPComponent in Langflow UI to connect to the MCP (Model Control Plane) server.

## Overview

The MCPComponent serves as a bridge between Langflow and the MCP server, allowing you to leverage all the capabilities of MCP models within your Langflow workflows. This includes chat models, completion models, filesystem operations, Git analysis, and Prometheus metrics.

## Installing the Component

Before using the component, make sure it's properly installed in your Langflow environment:

1. Copy the `mcp_component.py` file to your Langflow components directory
2. Update the `__init__.py` file to import the component
3. Restart Langflow to load the component

You can automate this process using the MCP runner script:

```bash
./mcp_run langflow install-component --component-dir=/path/to/component
```

## Using the Component in Langflow

### Step 1: Add the Component to Your Flow

1. Open Langflow UI (typically at http://localhost:7860)
2. Create a new flow
3. Find "MCPComponent" in the components panel (usually under "Custom")
4. Drag and drop the component onto the canvas

### Step 2: Configure the Component

The MCPComponent has several configuration options:

- **mcp_server_url**: URL of the MCP server (default: http://localhost:8000)
- **operation**: The type of operation to perform (chat, completion, git, filesystem, prometheus)
- **model_id**: ID of the model to use (optional, will default to an appropriate model for the operation)
- Additional parameters specific to each operation type

### Step 3: Connect Inputs and Outputs

The component can be connected to:

- **Input nodes** that provide parameters for the operations
- **Output nodes** that process the response from the MCP server

## Operation Examples

### Chat Operation

```json
{
  "mcp_server_url": "http://localhost:8000",
  "operation": "chat",
  "model_id": "openai-gpt-chat",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Give me a quick example of Python code."}
  ],
  "max_tokens": 150,
  "temperature": 0.7
}
```

### Completion Operation

```json
{
  "mcp_server_url": "http://localhost:8000",
  "operation": "completion",
  "model_id": "openai-gpt-completion",
  "prompt": "Write a function to sort a list in Python:",
  "max_tokens": 200,
  "temperature": 0.7
}
```

### Filesystem Operation

```json
{
  "mcp_server_url": "http://localhost:8000",
  "operation": "filesystem",
  "model_id": "filesystem",
  "path": ".",
  "operation": "ls"
}
```

### Git Analysis Operation

```json
{
  "mcp_server_url": "http://localhost:8000",
  "operation": "git",
  "model_id": "git-analyzer",
  "repo_url": "https://github.com/langchain-ai/langchain",
  "commit_sha": null
}
```

### Prometheus Operation

```json
{
  "mcp_server_url": "http://localhost:8000",
  "operation": "prometheus",
  "model_id": "prometheus",
  "query": "up",
  "timeframe": "5m",
  "analyze": true
}
```

## Example Workflows

### Simple Chat Bot

[Screenshot: Simple chat bot flow]

Components:
- TextInput (for user's message)
- MCPComponent (configured for chat operation)
- TextOutput (to display the assistant's response)

### Code Generation

[Screenshot: Code generation flow]

Components:
- TextInput (for prompt)
- MCPComponent (configured for completion operation)
- CodeOutput (to display and format the generated code)

### Repository Analysis

[Screenshot: Repository analysis flow]

Components:
- TextInput (for repository URL)
- MCPComponent (configured for git operation)
- JsonOutput (to display the analysis results)

## Troubleshooting

### Component Not Appearing

If the MCPComponent doesn't appear in Langflow:
- Make sure the component file is in the correct directory
- Check that it's properly imported in the `__init__.py` file
- Restart Langflow completely

### Connection Issues

If you're getting connection errors:
- Verify the MCP server is running
- Check the URL is correct
- Try a simple request to the server directly

### Parameter Errors

If you're getting parameter errors:
- Double-check that you're using the correct parameter names
- Ensure the parameters are formatted correctly
- Verify that the operation and model_id are compatible

## Advanced Usage

### Chaining Multiple Operations

You can chain multiple MCPComponent nodes together to create complex workflows:
1. Use one component for Git analysis
2. Pass the result to another component for AI processing
3. Generate a report with the findings

### Custom Models

If your MCP server has custom models not listed in the component's defaults:
1. Use the `list_models()` method to get available models
2. Specify the model ID in the component configuration
3. Pass the appropriate parameters for that model

## Testing the Component

You can test the component functionality using the provided test scripts:

```bash
# Run the test script to verify all functionality
python test_mcp_component_all_features.py

# Run the demo script to see operation examples
python mcp_component_demo.py

# Use the MCP runner script
./mcp_run langflow test-component --component-path=/path/to/mcp_component.py
```

## Further Resources

- [MCP Server Documentation](link_to_mcp_docs)
- [Langflow Documentation](https://docs.langflow.org)
- [Langflow Component Development Guide](link_to_component_dev_guide) 