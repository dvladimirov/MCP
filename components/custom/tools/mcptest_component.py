from langflow.custom import Component
from langflow.io import StrInput, MessageTextInput, Output
from langflow.schema import Data
from langflow.schema.message import Message
import socket
import os

class MCPTestComponent(Component):
    display_name = "MCP Test Component"
    description = "A simplified MCP test component."
    icon = "🧪"
    category = "Tools"
    name = "MCPTestComponent"

    def build(self):
        self.add_input(
            StrInput(
                id="mcp_url",
                name="MCP URL",
                description="URL of the MCP server. Use host.docker.internal instead of localhost if MCP server is on the host machine.",
                default="http://host.docker.internal:8000",
                required=True
            )
        )
        
        self.add_input(
            MessageTextInput(
                id="user_input",
                name="User Input",
                description="Text input to process",
                required=False
            )
        )
        
        self.add_output(
            Output(
                id="result",
                name="Result",
                description="Connection result"
            )
        )
    
    def _check_connection(self, url):
        """Check if the server is reachable"""
        try:
            # Extract the host and port from the URL
            if "://" in url:
                host = url.split("://")[1].split(":")[0]
                port_str = url.split("://")[1].split(":")[1].split("/")[0] if ":" in url.split("://")[1] else "80"
                port = int(port_str)
            else:
                host = url.split(":")[0]
                port = int(url.split(":")[1].split("/")[0]) if ":" in url else 80
            
            # Replace host.docker.internal with the actual IP if needed
            if host == "host.docker.internal":
                # On Linux, host.docker.internal might not be available by default
                try:
                    host = socket.gethostbyname("host.docker.internal")
                except socket.gaierror:
                    # Fallback to the Docker host gateway
                    host = os.environ.get("DOCKER_HOST_IP", "172.17.0.1")
            
            # Create a socket and try to connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            result = sock.connect_ex((host, port))
            sock.close()
            
            return result == 0  # 0 means connection successful
        except Exception as e:
            return False
    
    def process(self, data: Data) -> Message:
        mcp_url = data["inputs"].get("mcp_url", "http://host.docker.internal:8000")
        user_input = data["inputs"].get("user_input", "")
        
        # Check if we can connect to the server
        can_connect = self._check_connection(mcp_url)
        
        if can_connect:
            result_text = f"✅ Successfully connected to MCP at {mcp_url}"
        else:
            result_text = (
                f"🚫 Cannot connect to MCP server at {mcp_url}. Please check:\n"
                f"1. Is the MCP server running?\n"
                f"2. If your server is on the host machine, use 'host.docker.internal' instead of 'localhost'\n"
                f"3. Check if the port is correct and open"
            )
        
        if user_input:
            result_text += f"\nUser input: {user_input}"
            
        return Message(text=result_text) 