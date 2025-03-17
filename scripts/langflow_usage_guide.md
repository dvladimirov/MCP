# MCP Langflow Integration Guide

This guide explains how to use the MCP Langflow integration to create, manage, and test Langflow components that connect to the MCP server.

## Overview

The MCP (Model Control Plane) Langflow integration allows you to:

1. Generate a Langflow-compatible component based on the available models in your MCP server
2. Start and manage a Langflow server
3. Install the MCP component into Langflow
4. Test the component with chat requests

## Prerequisites

- MCP server should be up and running
- Python environment with `uv` installed
- (Optional) OpenAI API key for AI-assisted method generation

## Using the Interactive Menu

### 1. Access the Langflow Management Menu

Run the `mcp_run` script and select option 9 (Langflow Management):

```bash
./mcp_run
# Select option 9
```

The Langflow Management menu provides the following options:
- Start Langflow Server
- Stop Langflow Server
- Check Langflow Status
- Open Langflow in Browser
- Generate MCP Component for Langflow
- Install MCP Component in Langflow
- Test MCP Component Chat Functionality

### 2. Generate the MCP Component

From the Langflow Management menu, select option 5 (Generate MCP Component for Langflow). You'll be prompted for:

- Output directory (defaults to current directory)

The generator will:
1. Connect to your MCP server
2. Fetch all available models and their capabilities
3. Generate a Langflow-compatible component 
4. Create an example script

The generated files will be:
- `mcp_component.py`: The component code
- `mcp_component_example.py`: Example usage script

### 3. Start the Langflow Server

From the Langflow Management menu, select option 1 (Start Langflow Server). This will:

1. Install Langflow if it's not already installed
2. Start the Langflow server on port 7860
3. Display the URL to access the Langflow UI

### 4. Install the MCP Component in Langflow

From the Langflow Management menu, select option 6 (Install MCP Component in Langflow). You'll be prompted for:

- Component directory (where the generated files are located)

The installer will:
1. Copy the component to Langflow's custom components directory
2. Update the required imports
3. Optionally restart Langflow to apply the changes

### 5. Test the MCP Component

From the Langflow Management menu, select option 7 (Test MCP Component Chat Functionality). You'll be prompted for:

- Path to the component file

The test will:
1. Dynamically load the component
2. Connect to the MCP server
3. Find models with chat capability
4. Make a test chat request
5. Display the response

## Using Command Line Options

For batch operations or automation, you can use direct command line options:

### Generate a Component

```bash
./mcp_run langflow-component --output-dir=/path/to/output --server-url=http://localhost:8000
```

### Manage Langflow Server

```bash
# Start Langflow server
./mcp_run langflow start

# Stop Langflow server
./mcp_run langflow stop

# Check Langflow status
./mcp_run langflow status
```

### Install the Component

```bash
./mcp_run langflow install-component --component-dir=/path/to/component
```

### Test the Component

```bash
./mcp_run langflow test-component --component-path=/path/to/mcp_component.py
```

## Using the Component in Langflow UI

After installing the component:

1. Open Langflow UI in your browser (http://localhost:7860)
2. Create a new flow
3. Find the MCPComponent in the components panel
4. Drag the component onto the canvas
5. Configure its parameters:
   - `mcp_server_url`: URL of your MCP server
   - `operation`: The type of operation to perform (chat, completion, etc.)
   - `model_id`: The ID of the model to use
   - Additional parameters specific to the operation

## Troubleshooting

### Component Not Appearing in Langflow

If the component doesn't appear in Langflow after installation:

1. Make sure the component was installed correctly
2. Restart Langflow completely
3. Check Langflow logs for any errors

### Connection Issues

If the component can't connect to the MCP server:

1. Make sure the MCP server is running
2. Check that the server URL is correct
3. Verify network connectivity between Langflow and the MCP server

## Advanced Usage

### Creating Custom Components

You can modify the generated component or create your own based on it. Important aspects to consider:

1. The component must include the `@component` decorator
2. It should have a clear interface for interacting with the MCP server
3. Methods should return properly formatted responses

### Using AI-Assisted Generation

The component generator can use OpenAI to enhance method generation. To use this feature:

1. Set the `OPENAI_API_KEY` environment variable
2. Run the generator without the `--no-ai` flag 