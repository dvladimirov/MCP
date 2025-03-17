# MCP Langflow Component

This directory contains a Langflow-compatible component for the MCP (Model Control Plane) server.

## Files

- `mcp_component.py`: The main component file that provides the MCPComponent class.
- `mcp_component_example.py`: Example script showing how to use the component.

## Installation

1. Make sure you have the required dependencies:

```bash
pip install requests
```

2. If you want to use AI-assisted generation for custom methods:

```bash
pip install openai
```

3. Copy the files to your project directory.

## Usage

### Basic Usage

```python
from mcp_component import MCPComponent

# Initialize the component
mcp = MCPComponent(mcp_server_url="http://localhost:8000")

# List available models
models = mcp.list_models()
for model in models:
    print(f"- {model.get('id')}: {model.get('name')}")

# Use a specific capability (e.g., chat)
response = mcp.chat(
    model_id="openai-gpt-chat",  # or any other model ID supporting chat
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a joke about programming."}
    ],
    max_tokens=100,
    temperature=0.7
)
print(response)
```

### Universal Process Method

The component includes a universal `process` method that can be used for any capability:

```python
# Same as the chat example above, but using the process method
response = mcp.process(
    operation="chat",
    model_id="openai-gpt-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a joke about programming."}
    ],
    max_tokens=100,
    temperature=0.7
)
print(response)
```

## Supported Capabilities

The component dynamically generates methods based on the capabilities of the models in your MCP server. Typical capabilities include:

- `chat`: For chat-based interactions
- `completion`: For text completion
- `analyze`: For analyzing various inputs
- `search`: For searching content
- `diff`: For diff analysis

Run the example script to see all available capabilities on your server:

```bash
python mcp_component_example.py
```

## Integration with Langflow

The component includes a compatible decorator that allows it to be used with Langflow. See the Langflow documentation for details on how to integrate custom components.

## Customization

You can modify the generated component to add additional functionality or customize existing methods. The component is designed to be extensible and easy to modify. 