#!/usr/bin/env python3
# MCP AI Service Component

import json
import requests
import socket
import os

from langflow.custom import Component
from langflow.io import StrInput, DropdownInput, BoolInput, MessageTextInput, Output
from langflow.schema import Data
from langflow.schema.message import Message

class MCPComponent(Component):
    """Component for interacting with MCP models"""
    
    # Langflow UI display properties
    display_name = "MCP Component"
    description = "MCP server integration with Git diff analysis"
    documentation = "https://docs.example.com/mcp-git-diff-analyzer"
    icon = "🧠"
    category = "Tools"
    name = "MCPComponent"

    # Dynamic host options - add actual host machine's IP and all possible Docker options
    HOST_OPTIONS = [
        "localhost",           # Will work with network_mode: host
        "127.0.0.1",           # Will work with network_mode: host
        "host.docker.internal", # Works on Docker Desktop
        "172.17.0.1",          # Common Docker gateway
        "192.168.1.7",         # Host actual IP - most reliable for Docker 
    ]

    # Analysis types available in the MCP service
    ANALYSIS_TYPE_OPTIONS = [
        "basic",              # Basic diff analysis
        "requirements",       # Analysis with requirements details
        "full",               # Full detailed analysis
        "security",           # Security-focused analysis
    ]

    inputs = [
        DropdownInput(
            name="server_host",
            display_name="MCP Server Host",
            info="Host address of the MCP server. If using network_mode: host in docker-compose, localhost will work",
            options=HOST_OPTIONS,
            value="localhost",  # Default to localhost with network_mode: host
            required=True
        ),
        StrInput(
            name="server_port",
            display_name="MCP Server Port",
            info="Port of the MCP server",
            value="8000",
            required=True
        ),
        StrInput(
            name="repo_url",
            display_name="Repository URL",
            info="URL of the Git repository",
            value="https://github.com/username/repo",
            required=True
        ),
        StrInput(
            name="commit_sha",
            display_name="Commit SHA",
            info="SHA of the commit to analyze",
            value="",
            required=True
        ),
        DropdownInput(
            name="analysis_type",
            display_name="Analysis Type",
            info="Type of analysis to perform",
            options=ANALYSIS_TYPE_OPTIONS,
            value="requirements",  # Default to requirements analysis
            required=True
        ),
        BoolInput(
            name="include_dependencies",
            display_name="Include Dependencies",
            info="Whether to include dependency analysis",
            value=True,
            required=False
        ),
        BoolInput(
            name="include_compatibility",
            display_name="Include Compatibility Check",
            info="Whether to include compatibility analysis",
            value=True,
            required=False
        ),
        MessageTextInput(
            name="user_message",
            display_name="User Message",
            info="Optional message to include with the analysis",
            required=False
        )
    ]

    outputs = [
        Output(display_name="Analysis Result", name="result", method="process_inputs"),
    ]

    def _check_connection(self, host, port):
        """Check if the server is reachable"""
        try:
            # Create a socket and try to connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            result = sock.connect_ex((host, int(port)))
            sock.close()
            
            return result == 0  # 0 means connection successful
        except Exception as e:
            return False

    def process_inputs(self) -> Message:
        """Process the inputs and return a Message object that can connect to text outputs"""
        host = self.server_host
        port = self.server_port
        repo_url = self.repo_url
        commit_sha = self.commit_sha
        analysis_type = self.analysis_type
        include_dependencies = getattr(self, 'include_dependencies', True)
        include_compatibility = getattr(self, 'include_compatibility', True)
        user_message = self.user_message if hasattr(self, 'user_message') else ""
        
        # Build the server URL
        server_url = f"http://{host}:{port}"
        
        # First check if we can connect to the server
        if not self._check_connection(host, port):
            # Network mode diagnostics
            network_mode = self._detect_network_mode()
            
            # Try other hosts automatically
            alternative_hosts = []
            for alt_host in ["localhost", "127.0.0.1", "host.docker.internal", "172.17.0.1", "192.168.1.7"]:
                if alt_host != host and self._check_connection(alt_host, port):
                    alternative_hosts.append(alt_host)
            
            if network_mode == "host":
                connection_error = (
                    f"🚫 Cannot connect to MCP server at {server_url}.\n\n"
                    f"You are using network_mode: host, so localhost/127.0.0.1 should work if the server is running.\n"
                    f"Common causes and solutions:\n"
                    f"1. The MCP server isn't running - Start the server\n"
                    f"2. The server is running on a different port - Check the port\n"
                )
            else:
                connection_error = (
                    f"🚫 Cannot connect to MCP server at {server_url}.\n\n"
                    f"Common causes and solutions:\n"
                    f"1. The MCP server isn't running - Start the server\n"
                    f"2. The MCP server is running on 127.0.0.1 only - Restart it with '--host 0.0.0.0'\n"
                    f"3. Try using your host machine's actual IP: 192.168.1.7\n"
                    f"4. Restart Docker with network_mode: host in docker-compose.yml\n"
                )
            
            if alternative_hosts:
                connection_error += f"\n✅ Working alternatives detected! Try these hosts instead:\n"
                for alt in alternative_hosts:
                    connection_error += f"- {alt}\n"
            
            return Message(text=connection_error)
        
        try:
            # Validate inputs
            if not repo_url:
                return Message(text="Error: Repository URL is required for Git diff analysis")
            
            if not commit_sha:
                return Message(text="Error: Commit SHA is required for Git diff analysis")
            
            # Select the appropriate endpoint based on analysis type
            if analysis_type == "requirements":
                endpoint = "/v1/models/git-diff-analyzer/analyze-requirements"
            elif analysis_type == "security":
                endpoint = "/v1/models/git-diff-analyzer/analyze-security"
            elif analysis_type == "full":
                endpoint = "/v1/models/git-diff-analyzer/analyze-full"
            else:
                # Default to basic analysis
                endpoint = "/v1/models/git-diff-analyzer/analyze"
            
            # Construct the full API endpoint
            url = f"{server_url}{endpoint}"
            
            # Prepare the enhanced payload with all parameters
            payload = {
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "analysis_type": analysis_type,
                "options": {
                    "include_dependencies": include_dependencies,
                    "include_compatibility": include_compatibility,
                    "detailed": True,  # Always get detailed results
                }
            }
            
            # Make the API call
            response = requests.post(url, json=payload, timeout=30)
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                response_text = json.dumps(result, indent=2)
                if user_message:
                    response_text = f"User message: {user_message}\n\n{response_text}"
                return Message(text=response_text)
            elif response.status_code == 404:
                # Handle the case where the specific endpoint isn't available
                # Try the standard endpoint as fallback
                fallback_url = f"{server_url}/v1/models/git-diff-analyzer/analyze"
                fallback_response = requests.post(fallback_url, json={"repo_url": repo_url, "commit_sha": commit_sha}, timeout=30)
                
                if fallback_response.status_code == 200:
                    result = fallback_response.json()
                    response_text = json.dumps(result, indent=2)
                    response_text = f"Note: Detailed {analysis_type} analysis not available. Showing basic analysis instead.\n\n{response_text}"
                    return Message(text=response_text)
                else:
                    error_message = (
                        f"Error: The requested analysis type '{analysis_type}' is not available and fallback also failed.\n"
                        f"Status code: {response.status_code}, Message: {response.text}\n"
                        f"Try using the 'basic' analysis type instead."
                    )
                    return Message(text=error_message)
            else:
                error_message = f"Error: Failed to analyze Git diff. Status code: {response.status_code}, Message: {response.text}"
                return Message(text=error_message)
                
        except requests.exceptions.ConnectionError as e:
            return Message(text=f"Connection Error: Could not connect to {server_url}. Is the MCP server running? Error details: {str(e)}")
        except Exception as e:
            return Message(text=f"Error: {str(e)}")
    
    def _detect_network_mode(self):
        """Try to detect if we're running in host network mode"""
        try:
            # In host network mode, we can access localhost directly
            if self._check_connection("localhost", self.server_port) or self._check_connection("127.0.0.1", self.server_port):
                return "host"
                
            # Try to check container IP vs host IP
            container_ip = socket.gethostbyname(socket.gethostname())
            if container_ip == "127.0.0.1" or container_ip.startswith("192.168."):
                return "host"
                
            return "bridge"  # Default mode
        except:
            return "unknown"
            
    def _get_container_network_info(self):
        """Get network information from inside the container"""
        try:
            # Get container's IP address
            container_ip = socket.gethostbyname(socket.gethostname())
            
            # Try to resolve host.docker.internal
            host_docker_internal = None
            try:
                host_docker_internal = socket.gethostbyname("host.docker.internal")
            except:
                pass
                
            # Get gateway IP
            gateway_ip = None
            try:
                with open('/proc/net/route') as f:
                    for line in f:
                        fields = line.strip().split()
                        if fields[1] == '00000000':  # Default route
                            gateway_ip = socket.inet_ntoa(bytes.fromhex(fields[2].zfill(8))[::-1])
                            break
            except:
                pass
                
            return {
                "container_ip": container_ip,
                "host_docker_internal": host_docker_internal,
                "gateway_ip": gateway_ip
            }
        except Exception as e:
            return {"error": str(e)} 