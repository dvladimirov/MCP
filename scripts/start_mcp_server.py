#!/usr/bin/env python3
"""
Convenient script to start the MCP server with configurable settings
"""

import os
import sys
import argparse
import uvicorn

def start_server(prometheus_url=None, host="127.0.0.1", port=8000, reload=True, debug=False):
    """Start the MCP server with the specified Prometheus URL"""
    
    # Set environment variables if provided
    if prometheus_url:
        print(f"Setting Prometheus URL to: {prometheus_url}")
        os.environ["PROMETHEUS_URL"] = prometheus_url
        
        # Verify the environment variable was set
        print(f"Verification - PROMETHEUS_URL is now: {os.getenv('PROMETHEUS_URL')}")
    else:
        current_url = os.getenv("PROMETHEUS_URL")
        if current_url:
            print(f"Using existing PROMETHEUS_URL from environment: {current_url}")
        else:
            print("PROMETHEUS_URL not set. Will use default: http://localhost:9090")
    
    # Display debug info if requested
    if debug:
        print("\nEnvironment Variables:")
        for key, value in os.environ.items():
            if key.startswith("PROMETHEUS") or key.startswith("MCP"):
                print(f"  {key}={value}")
    
    print(f"Starting MCP server on {host}:{port}")
    if reload:
        print("Hot reload is enabled - code changes will automatically restart the server")
    
    # Start the server using uvicorn
    uvicorn.run(
        "mcp_server:app",
        host=host,
        port=port,
        reload=reload
    )

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start the MCP server with configurable settings")
    parser.add_argument("--prometheus-url", help="URL of the Prometheus server", 
                       default=os.getenv("PROMETHEUS_URL"))
    parser.add_argument("--host", help="Host to bind the server to", default="127.0.0.1")
    parser.add_argument("--port", help="Port to bind the server to", type=int, default=8000)
    parser.add_argument("--no-reload", help="Disable hot reload", action="store_true")
    parser.add_argument("--debug", help="Show debug information", action="store_true")
    
    args = parser.parse_args()
    
    # Start the server with the provided arguments
    start_server(
        prometheus_url=args.prometheus_url,
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        debug=args.debug
    ) 