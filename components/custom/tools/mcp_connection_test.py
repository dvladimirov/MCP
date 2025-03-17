#!/usr/bin/env python3
# MCP Connection Test Component

import json
import requests
import socket
import os
import subprocess
import platform

from langflow.custom import Component
from langflow.io import StrInput, BoolInput, MessageTextInput, Output
from langflow.schema import Data
from langflow.schema.message import Message

class MCPConnectionTest(Component):
    """Component for testing MCP server connections"""
    
    # Langflow UI display properties
    display_name = "MCP Connection Test"
    description = "Test different ways to connect to the MCP server and provide diagnostics"
    icon = "🔌"
    category = "Tools"
    name = "MCPConnectionTest"

    inputs = [
        StrInput(
            name="server_host",
            display_name="Server Host",
            info="Host address of the MCP server (try: localhost, 127.0.0.1, host.docker.internal, or your machine's IP)",
            value="host.docker.internal",
            required=True
        ),
        StrInput(
            name="server_port",
            display_name="Server Port",
            info="Port of the MCP server",
            value="8000",
            required=True
        ),
        BoolInput(
            name="run_diagnostics",
            display_name="Run Network Diagnostics",
            info="Run additional network diagnostics",
            value=True
        ),
        MessageTextInput(
            name="user_message",
            display_name="User Message",
            info="Optional message to include with the test",
            required=False
        )
    ]

    outputs = [
        Output(display_name="Test Result", name="result", method="test_connection"),
    ]

    def _ping_host(self, host):
        """Try to ping the host to check connectivity"""
        try:
            # Different ping command based on OS
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', host]
            
            # Execute the ping command
            result = subprocess.run(command, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   timeout=2)
            
            # Check if the ping was successful
            return result.returncode == 0
        except Exception as e:
            return False

    def _check_socket_connection(self, host, port):
        """Try to establish a direct socket connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            return result == 0, result  # 0 means success
        except Exception as e:
            return False, str(e)

    def _try_http_connection(self, url):
        """Try to make an HTTP connection to the server"""
        try:
            response = requests.get(url, timeout=2)
            return True, response.status_code
        except requests.exceptions.ConnectionError as e:
            return False, "Connection error"
        except requests.exceptions.Timeout:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)

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

    def test_connection(self) -> Message:
        """Test connecting to the MCP server with detailed diagnostics"""
        host = self.server_host
        port = self.server_port
        run_diagnostics = self.run_diagnostics
        user_message = self.user_message if hasattr(self, 'user_message') else ""
        
        results = []
        
        # Add user message if provided
        if user_message:
            results.append(f"User message: {user_message}")
        
        # Store connection results
        connection_details = {}
        
        # Try direct socket connection
        can_connect, socket_result = self._check_socket_connection(host, port)
        connection_details["socket_connection"] = {
            "success": can_connect,
            "result": socket_result
        }
        
        # Try HTTP connections with different protocols
        http_url = f"http://{host}:{port}"
        https_url = f"https://{host}:{port}"
        
        http_success, http_result = self._try_http_connection(http_url)
        connection_details["http_connection"] = {
            "success": http_success,
            "result": http_result
        }
        
        https_success, https_result = self._try_http_connection(https_url)
        connection_details["https_connection"] = {
            "success": https_success,
            "result": https_result
        }
        
        # Comprehensive report
        if can_connect or http_success or https_success:
            results.append(f"✅ Successfully connected to MCP server at {host}:{port}")
            
            if can_connect:
                results.append("✓ Socket connection: Successful")
            else:
                results.append("⚠️ Socket connection: Failed")
                
            if http_success:
                results.append(f"✓ HTTP connection: Successful (Status {http_result})")
            else:
                results.append("⚠️ HTTP connection: Failed")
                
            if https_success:
                results.append(f"✓ HTTPS connection: Successful (Status {https_result})")
            else:
                results.append("⚠️ HTTPS connection: Failed")
        else:
            results.append(f"🚫 Cannot connect to MCP server at {host}:{port}")
            
            # Try alternative hosts if the given one failed
            alternative_hosts = []
            
            if host != "localhost" and host != "127.0.0.1":
                alternative_hosts.append("localhost")
                alternative_hosts.append("127.0.0.1")
            
            if host != "host.docker.internal":
                alternative_hosts.append("host.docker.internal")
                
            if host != "172.17.0.1":
                alternative_hosts.append("172.17.0.1")
            
            # Try container's gateway (common for Docker)
            network_info = self._get_container_network_info()
            if "gateway_ip" in network_info and network_info["gateway_ip"] and network_info["gateway_ip"] not in alternative_hosts:
                alternative_hosts.append(network_info["gateway_ip"])
            
            # Add results for alternative hosts
            alt_results = []
            for alt_host in alternative_hosts:
                alt_can_connect, _ = self._check_socket_connection(alt_host, port)
                if alt_can_connect:
                    alt_results.append(f"✅ Alternative host {alt_host}:{port} is reachable!")
                    alt_results.append(f"⚠️ Try changing your server_host to '{alt_host}' instead")
            
            if alt_results:
                results.append("\n🔍 Alternative hosts tested:")
                results.extend(alt_results)
        
        # Only run extensive diagnostics if requested
        if run_diagnostics:
            results.append("\n📊 Network Diagnostics:")
            
            # Check if host.docker.internal is configured properly
            try:
                docker_internal_ip = socket.gethostbyname("host.docker.internal")
                results.append(f"✓ host.docker.internal resolves to {docker_internal_ip}")
            except socket.gaierror:
                results.append("⚠️ host.docker.internal is not properly configured")
            
            # Add container network information
            results.append("\n🖧 Container Network Information:")
            for key, value in self._get_container_network_info().items():
                results.append(f"- {key}: {value}")
            
            # Check ping to the host
            ping_result = self._ping_host(host)
            if ping_result:
                results.append(f"✓ Ping to {host} successful")
            else:
                results.append(f"⚠️ Ping to {host} failed")
            
            # Add recommendations
            results.append("\n📋 Recommendations:")
            results.append("1. Make sure your MCP server is running on 0.0.0.0 instead of just 127.0.0.1")
            results.append("2. Check for any firewalls blocking connections between Docker and host")
            results.append("3. Try using your machine's actual LAN IP instead of localhost or host.docker.internal")
            results.append("4. If using Linux, ensure host.docker.internal is properly configured or use the gateway IP")
        
        return Message(text="\n".join(results)) 