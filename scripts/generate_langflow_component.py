#!/usr/bin/env python3
"""
Generate Langflow Component Script

This script generates a Langflow-compatible component based on the available models in the MCP server.
It fetches all models from the MCP server and creates appropriate wrapper methods for each model.
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import shutil

# Add the parent directory to Python path for proper imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Try to import OpenAI for help with generation
    import openai
    HAVE_OPENAI = True
except ImportError:
    HAVE_OPENAI = False

def check_langflow_installed() -> bool:
    """Check if langflow is installed in the current environment"""
    try:
        import langflow
        return True
    except ImportError:
        return False

def fetch_models(server_url: str = "http://localhost:8000") -> List[Dict[str, Any]]:
    """Fetch available models from the MCP server
    
    Args:
        server_url: URL of the MCP server
        
    Returns:
        List of model dictionaries
    """
    try:
        response = requests.get(f"{server_url}/v1/models")
        response.raise_for_status()
        return response.json().get("models", [])
    except Exception as e:
        print(f"Error fetching models from MCP server: {e}")
        return []

def generate_component(models: List[Dict[str, Any]], 
                       output_dir: str, 
                       server_url: str = "http://localhost:8000",
                       use_ai_assistance: bool = True) -> bool:
    """Generate langflow component based on models
    
    Args:
        models: List of model dictionaries
        output_dir: Directory to write output files
        server_url: URL of the MCP server
        use_ai_assistance: Whether to use OpenAI to help generate method code
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not models:
        print("No models found. Cannot generate component.")
        return False
    
    # Check if MCP server is accessible
    try:
        response = requests.get(f"{server_url}/v1/models")
        response.raise_for_status()
    except Exception as e:
        print(f"Warning: MCP server at {server_url} is not accessible: {e}")
        print("The generated component will expect the server to be available when used.")
    
    # Make sure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Group models by capability
    grouped_models = {}
    for model in models:
        capabilities = model.get("capabilities", [])
        model_id = model.get("id", "unknown")
        for capability in capabilities:
            if capability not in grouped_models:
                grouped_models[capability] = []
            grouped_models[capability].append(model_id)
    
    component_path = os.path.join(output_dir, "mcp_component.py")
    example_path = os.path.join(output_dir, "mcp_component_example.py")
    
    # Generate the base component code
    base_code = generate_base_code(models, server_url)
    
    # Generate method code for each capability
    method_code = ""
    for capability, model_ids in grouped_models.items():
        # Create a method for each capability
        if use_ai_assistance and HAVE_OPENAI and "OPENAI_API_KEY" in os.environ:
            # Use AI to generate the method
            generated_method = generate_method_with_ai(capability, model_ids, models)
            if generated_method:
                method_code += f"\n{generated_method}\n"
            else:
                # If AI generation failed, use the generic method
                method_code += generate_method_code(capability, model_ids, models)
        else:
            # Use generic method generation
            method_code += generate_method_code(capability, model_ids, models)
    
    # Generate process method that can handle all inputs
    process_method = generate_process_method(grouped_models)
    
    # Combine all code
    full_code = f"{base_code}\n{method_code}\n{process_method}"
    
    # Write component to file
    try:
        with open(component_path, "w") as f:
            f.write(full_code)
        print(f"\n✅ Component written to: {component_path}")
        
        # Generate example code
        example_code = generate_example_code(models, grouped_models)
        with open(example_path, "w") as f:
            f.write(example_code)
        print(f"✅ Example code written to: {example_path}")
        
        # Also copy the test script to the output directory
        test_script_src = os.path.join(parent_dir, "test_mcp_component_all_features.py")
        if os.path.exists(test_script_src):
            test_script_dst = os.path.join(output_dir, "test_mcp_component_all_features.py")
            shutil.copy2(test_script_src, test_script_dst)
            print(f"✅ Test script copied to: {test_script_dst}")
        
        print("\n🔍 Next steps:")
        print("1) Install the component in Langflow with:")
        print(f"   ./mcp_run langflow install-component --component-dir={output_dir}")
        print("2) Test the component with:")
        print(f"   ./mcp_run langflow test-component --component-path={component_path}")
        
        return True
    except Exception as e:
        print(f"❌ Error writing component to file: {e}")
        return False

def generate_base_code(models: List[Dict[str, Any]], server_url: str) -> str:
    """Generate the base code for the component
    
    Args:
        models: List of model dictionaries
        server_url: URL of the MCP server
        
    Returns:
        str: Base code string
    """
    model_ids = ", ".join(f'"{model.get("id")}"' for model in models)
    model_names = {}
    for model in models:
        model_id = model.get("id")
        model_name = model.get("name", model_id)
        model_names[model_id] = model_name
    
    # Format model names as JSON with proper indentation
    model_names_json = json.dumps(model_names, indent=4)
    
    return f"""#!/usr/bin/env python3
# Generated by MCP Langflow Component Generator
# Date: {datetime.now().isoformat()}

import os
import json
import requests
from typing import Dict, List, Any, Optional

def component(cls):
    \"\"\"Simple component decorator for compatibility\"\"\"
    return cls

@component
class MCPComponent:
    \"\"\"Component for interacting with MCP models\"\"\"
    
    def __init__(self, mcp_server_url: str = "{server_url}"):
        self.mcp_server_url = mcp_server_url
        self.available_models = self._fetch_available_models()
        
        # Known model IDs from server
        self.known_models = [{model_ids}]
        
        # Model display names
        self.model_names = {model_names_json}
    
    def _fetch_available_models(self) -> List[Dict[str, Any]]:
        \"\"\"Fetch available models from the MCP server\"\"\"
        try:
            response = requests.get(f"{{self.mcp_server_url}}/v1/models")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            print(f"Error fetching models from MCP server: {{e}}")
            return []
    
    def list_models(self) -> List[Dict[str, Any]]:
        \"\"\"Return list of available models\"\"\"
        return self.available_models
"""

def generate_method_code(capability: str, model_ids: List[str], models: List[Dict[str, Any]]) -> str:
    """Generate method code for a specific capability
    
    Args:
        capability: Model capability
        model_ids: List of model IDs with this capability
        models: Full list of models
        
    Returns:
        str: Method code string
    """
    # Convert capability to a method name
    method_name = capability.lower().replace('-', '_')
    
    # Get the first model with this capability for parameter inspection
    model_id = model_ids[0] if model_ids else None
    model_details = next((m for m in models if m.get("id") == model_id), {})
    
    # Create a parameter list from the model's input schema if available
    input_schema = model_details.get("input_schema", {})
    parameters = input_schema.get("parameters", [])
    
    # If no parameters are found in the schema, add default parameters based on the capability
    if not parameters and capability == "chat":
        parameters = [
            {"name": "messages", "type": "List[Dict[str, str]]", "description": "List of message objects with role and content"}
        ]
    elif not parameters and capability == "completion":
        parameters = [
            {"name": "prompt", "type": "str", "description": "Text prompt for completion"}
        ]
    
    # Create method signature and docstring
    method_signature = f"    def {method_name}(self, model_id: str = None"
    
    # Add parameters to the signature
    for param in parameters:
        param_name = param.get("name", "")
        param_type = param.get("type", "Any")
        param_default = param.get("default", None)
        
        # Skip model_id as it's already in the signature
        if param_name == "model_id":
            continue
            
        # Add the parameter to the signature
        if param_default is not None:
            method_signature += f", {param_name}: {param_type} = {repr(param_default)}"
        else:
            method_signature += f", {param_name}: {param_type}"
    
    # Close the method signature
    method_signature += ") -> Dict[str, Any]:"
    
    # Add docstring
    docstring = f"""
        \"\"\"Execute a {capability} operation using the specified model
        
        Args:
            model_id: ID of the model to use (must support {capability})
"""
    
    # Add parameter docs
    for param in parameters:
        param_name = param.get("name", "")
        param_desc = param.get("description", f"{param_name} parameter")
        
        # Skip model_id as it's already documented
        if param_name == "model_id":
            continue
            
        docstring += f"            {param_name}: {param_desc}\n"
    
    docstring += """            
        Returns:
            Dict[str, Any]: Operation result
        \"\"\""""
    
    # Create method implementation
    method_impl = f"""
        # Use the first available model for this capability if none specified
        if model_id is None:
            # Available models for {capability}
            available_models = {json.dumps(model_ids)}
            if available_models:
                model_id = available_models[0]
            else:
                raise ValueError(f"No models available for {capability}")
        
        # Make sure the model supports this capability
        if model_id not in {json.dumps(model_ids)}:
            raise ValueError(f"Model {{model_id}} does not support {capability}")
        
        # Prepare the payload
        payload = {{'model_id': model_id}}
"""
    
    # Add parameters to the payload
    for param in parameters:
        param_name = param.get("name", "")
        if param_name != "model_id":
            method_impl += f"""
        if {param_name} is not None:
            payload['{param_name}'] = {param_name}
"""
    
    # Add the API call
    method_impl += f"""
        # Call the appropriate endpoint
        endpoint = f"{{self.mcp_server_url}}/v1/models/{{model_id}}/{capability}"
        
        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {{
                "status": "error",
                "error": str(e),
                "data": None
            }}
"""
    
    # Combine all parts of the method
    return f"{method_signature}{docstring}{method_impl}"

def generate_process_method(grouped_models: Dict[str, List[str]]) -> str:
    """Generate a universal process method that can route to appropriate methods
    
    Args:
        grouped_models: Dictionary of capabilities to model IDs
        
    Returns:
        str: Process method code
    """
    # Create operation type enum values
    operations = ", ".join(f'"{capability}"' for capability in grouped_models.keys())
    
    # Create the method
    return f"""
    def process(self, 
                operation: str,
                model_id: Optional[str] = None,
                **kwargs) -> Dict[str, Any]:
        \"\"\"Process a request through the appropriate method based on operation type
        
        Args:
            operation: Type of operation to perform ({", ".join(grouped_models.keys())})
            model_id: ID of the model to use
            **kwargs: Additional parameters for the operation
            
        Returns:
            Dict[str, Any]: Operation result
        \"\"\"
        
        # Map operation to method
        operation_methods = {{
            {", ".join([f'"{op}": self.{op.lower().replace("-", "_")}' for op in grouped_models.keys()])}
        }}
        
        # Check if the operation is supported
        if operation not in operation_methods:
            available_ops = ["{', '.join(grouped_models.keys())}"]
            raise ValueError(f"Unsupported operation: {{operation}}. Available operations: {{available_ops}}")
            
        # Call the appropriate method
        return operation_methods[operation](model_id=model_id, **kwargs)
"""

def generate_example_code(models: List[Dict[str, Any]], grouped_models: Dict[str, List[str]]) -> str:
    """Generate example code for using the component
    
    Args:
        models: List of model dictionaries
        grouped_models: Dictionary of capabilities to model IDs
        
    Returns:
        str: Example code string
    """
    examples = ""
    
    # Generate example for each capability
    for capability, model_ids in grouped_models.items():
        if not model_ids:
            continue
            
        model_id = model_ids[0]
        method_name = capability.lower().replace('-', '_')
        
        # Get model details
        model_details = next((m for m in models if m.get("id") == model_id), {})
        
        # Create a sample call based on the capability
        if capability == "chat":
            examples += f"""
# Example of {capability} with {model_id}
print("\\nTesting {capability} with {model_id}...")
try:
    response = mcp.{method_name}(
        model_id="{model_id}",
        messages=[
            {{"role": "system", "content": "You are a helpful assistant."}},
            {{"role": "user", "content": "Tell me a brief joke about programming."}}
        ],
        max_tokens=100,
        temperature=0.7
    )
    print(f"Response: {{json.dumps(response, indent=2)}}")
except Exception as e:
    print(f"Error: {{e}}")
"""
        elif capability == "completion":
            examples += f"""
# Example of {capability} with {model_id}
print("\\nTesting {capability} with {model_id}...")
try:
    response = mcp.{method_name}(
        model_id="{model_id}",
        prompt="Write a function in Python to calculate the factorial of a number:",
        max_tokens=150,
        temperature=0.7
    )
    print(f"Response: {{json.dumps(response, indent=2)}}")
except Exception as e:
    print(f"Error: {{e}}")
"""
        else:
            # For other capabilities, provide a minimal example
            examples += f"""
# Example of {capability} with {model_id}
print("\\nTesting {capability} with {model_id}...")
try:
    response = mcp.{method_name}(model_id="{model_id}")
    print(f"Response: {{json.dumps(response, indent=2)}}")
except Exception as e:
    print(f"Error: {{e}}")
"""
    
    # Create the full example
    return f"""#!/usr/bin/env python3
# Example usage of the MCP Component
# Generated by MCP Langflow Component Generator
# Date: {datetime.now().isoformat()}

import os
import json
from mcp_component import MCPComponent

def main():
    # Initialize the component
    print("Initializing MCPComponent...")
    mcp = MCPComponent(mcp_server_url="http://localhost:8000")
    
    # List available models
    print("\\nAvailable models:")
    models = mcp.list_models()
    for model in models:
        capabilities = ', '.join(model.get('capabilities', []))
        print(f"- {{model.get('id')}}: {{model.get('name')}} (Capabilities: {{capabilities}})")
{examples}

if __name__ == "__main__":
    main()
"""

def generate_method_with_ai(capability: str, model_ids: List[str], models: List[Dict[str, Any]]) -> Optional[str]:
    """Generate method code using OpenAI assistance
    
    Args:
        capability: Model capability
        model_ids: List of model IDs with this capability
        models: Full list of models
        
    Returns:
        Optional[str]: Method code string or None if generation fails
    """
    if not HAVE_OPENAI or "OPENAI_API_KEY" not in os.environ:
        return None
        
    try:
        client = openai.OpenAI()
        
        # Get the first model with this capability for parameter inspection
        model_id = model_ids[0] if model_ids else None
        model_details = next((m for m in models if m.get("id") == model_id), {})
        
        # Create a parameter list from the model's input schema if available
        input_schema = model_details.get("input_schema", {})
        parameters = input_schema.get("parameters", [])
        
        # Create a prompt for the AI
        prompt = f"""Generate a Python method for a class called MCPComponent that implements the '{capability}' capability.

The method should be named '{capability.lower().replace('-', '_')}' and should accept the following parameters:
- model_id: str (optional, default=None) - The ID of the model to use
{chr(10).join(['- ' + param.get('name') + ': ' + param.get('type', 'Any') + ' - ' + param.get('description', '') for param in parameters if param.get('name') != 'model_id'])}

The method should:
1. If model_id is None, use the first available model from this list: {model_ids}
2. Check if the provided model_id is in the list of supported models
3. Prepare a payload with all parameters
4. Make a POST request to: {{self.mcp_server_url}}/v1/models/{{model_id}}/{capability}
5. Handle errors appropriately
6. Return the JSON response from the server

Format the method with proper docstrings, error handling, and follow Python best practices.
ONLY return the method code, not the entire class or any explanations.
"""
        
        # Generate the method code
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Python expert focused on creating clean, well-documented code."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        
        # Extract the method code
        method_code = response.choices[0].message.content.strip()
        
        # Clean up the code if it has markdown formatting
        if method_code.startswith("```python"):
            method_code = method_code.split("```python", 1)[1]
        if method_code.endswith("```"):
            method_code = method_code.rsplit("```", 1)[0]
            
        method_code = method_code.strip()
        
        return method_code
    except Exception as e:
        print(f"Error generating method with AI: {e}")
        return None

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Generate Langflow component from MCP models")
    
    parser.add_argument("-s", "--server-url", default="http://localhost:8000",
                        help="URL of the MCP server (default: http://localhost:8000)")
    
    parser.add_argument("-o", "--output-dir", default=".",
                        help="Directory to write output files (default: current directory)")
    
    parser.add_argument("--no-ai", action="store_true",
                        help="Disable AI assistance for method generation")
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    print(f"MCP Langflow Component Generator")
    print(f"--------------------------------")
    print(f"Server URL: {args.server_url}")
    print(f"Output directory: {args.output_dir}")
    print(f"AI assistance: {'disabled' if args.no_ai else 'enabled'}")
    print()
    
    # Fetch models from the server
    print("Fetching models from MCP server...")
    models = fetch_models(args.server_url)
    
    if not models:
        print("No models found. Exiting.")
        return 1
    
    print(f"Found {len(models)} models.")
    for model in models:
        model_id = model.get("id", "unknown")
        model_name = model.get("name", model_id)
        capabilities = ", ".join(model.get("capabilities", []))
        print(f"- {model_id}: {model_name} (Capabilities: {capabilities})")
    
    # Generate the component
    print("\nGenerating component...")
    success = generate_component(
        models=models,
        output_dir=args.output_dir,
        server_url=args.server_url,
        use_ai_assistance=not args.no_ai
    )
    
    if success:
        print("\nComponent generation completed successfully!")
        return 0
    else:
        print("\nComponent generation failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 