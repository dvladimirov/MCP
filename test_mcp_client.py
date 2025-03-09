import os
import requests
import json
from typing import Dict, List, Any

def test_mcp_server(base_url: str = "http://localhost:8000"):
    """Test the MCP server with both Azure OpenAI and standard OpenAI."""
    
    # Test listing models
    print("Testing list models endpoint...")
    models_response = requests.get(f"{base_url}/v1/models")
    if models_response.status_code == 200:
        models = models_response.json().get("models", [])
        print(f"Available models: {json.dumps(models, indent=2)}")
    else:
        print(f"Error listing models: {models_response.status_code}")
        return
    
    # Test OpenAI chat completion
    print("\nTesting OpenAI chat completion...")
    chat_payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me a brief joke about programming."}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    chat_response = requests.post(
        f"{base_url}/v1/models/openai-gpt-chat/chat",
        json=chat_payload
    )
    
    if chat_response.status_code == 200:
        result = chat_response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"Chat response: {content}")
    else:
        print(f"Error with chat completion: {chat_response.status_code}")
        print(chat_response.text)
    
    # Test OpenAI text completion
    print("\nTesting OpenAI text completion...")
    completion_payload = {
        "prompt": "Write a function in Python to calculate the factorial of a number:",
        "max_tokens": 150,
        "temperature": 0.7
    }
    
    completion_response = requests.post(
        f"{base_url}/v1/models/openai-gpt-completion/completion",
        json=completion_payload
    )
    
    if completion_response.status_code == 200:
        result = completion_response.json()
        text = result["choices"][0]["text"]
        print(f"Completion response: {text}")
    else:
        print(f"Error with text completion: {completion_response.status_code}")
        print(completion_response.text)

if __name__ == "__main__":
    # Ensure your environment variables are set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable is not set")
    
    test_mcp_server() 