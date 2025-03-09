# MCP Components

This directory contains the core Model Control Plane (MCP) components used by the MCP server.

## Structure

- `__init__.py` - Package initialization
- `model.py` - Contains the ModelInfo and ModelCapability classes
- `server.py` - Implements the core MCPServer class
- `git_service.py` - Provides Git repository analysis services

## Usage

These components are used internally by the MCP server but can also be imported directly:

```python
from mcp.model import ModelInfo, ModelCapability
from mcp.server import MCPServer
from mcp.git_service import GitService, GitRepository

# Create an MCP server instance
server = MCPServer()

# Register a model
model = ModelInfo(
    id="my-model",
    name="My Custom Model",
    description="A custom model for MCP",
    capabilities=[ModelCapability.CHAT],
    context_length=4096
)
server.register_model(model)

# List registered models
models = server.list_models()

# Use the Git service
repo_analysis = GitService.analyze_repository("https://github.com/username/repository")
```

## Integration with LangFlow

The MCP components can be used with LangFlow through the `MCPAIComponent` class. See the main README for more details on how to integrate with LangFlow. 