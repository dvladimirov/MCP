#!/usr/bin/env python3
"""
MCP Memory Dashboard - A Prometheus Memory Monitoring Dashboard using MCP
"""

import os
import sys
import time
import json
import curses
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import the MCP client
from langflow import MCPAIComponent

class MemoryDashboard:
    """Memory monitoring dashboard using Prometheus MCP integration"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000", 
                 prometheus_url: str = "http://localhost:9090",
                 refresh_interval: int = 5):
        """Initialize the dashboard
        
        Args:
            mcp_server_url: URL of the MCP server
            prometheus_url: URL of the Prometheus server
            refresh_interval: Dashboard refresh interval in seconds
        """
        self.mcp_server_url = mcp_server_url
        self.prometheus_url = prometheus_url
        self.refresh_interval = refresh_interval
        self.mcp = MCPAIComponent(mcp_server_url=mcp_server_url)
        
        # Set the Prometheus URL in the environment
        os.environ["PROMETHEUS_URL"] = prometheus_url
        
        # Store the latest data
        self.latest_data = {
            "system_memory": {},
            "container_memory": {},
            "alerts": [],
            "last_update": None
        }
    
    def fetch_system_memory(self) -> Dict[str, Any]:
        """Fetch system memory metrics from Prometheus"""
        try:
            # Get total memory
            total_mem_result = self.mcp.prometheus_query("node_memory_MemTotal_bytes")
            available_mem_result = self.mcp.prometheus_query("node_memory_MemAvailable_bytes")
            
            # Calculate usage percentage
            usage_pct_result = self.mcp.prometheus_query(
                "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100"
            )
            
            # Process results
            hosts = {}
            
            if usage_pct_result.get('status') == 'success':
                results = usage_pct_result.get('data', {}).get('result', [])
                
                for result in results:
                    instance = result.get('metric', {}).get('instance', 'unknown')
                    try:
                        usage_pct = float(result.get('value', [0, 0])[1])
                        
                        # Find matching total and available memory
                        total_mem = next(
                            (float(r.get('value', [0, 0])[1]) for r in 
                             total_mem_result.get('data', {}).get('result', [])
                             if r.get('metric', {}).get('instance') == instance),
                            0
                        )
                        
                        available_mem = next(
                            (float(r.get('value', [0, 0])[1]) for r in 
                             available_mem_result.get('data', {}).get('result', [])
                             if r.get('metric', {}).get('instance') == instance),
                            0
                        )
                        
                        # Convert to GB
                        total_gb = total_mem / (1024 * 1024 * 1024)
                        available_gb = available_mem / (1024 * 1024 * 1024)
                        used_gb = total_gb - available_gb
                        
                        # Determine status
                        if usage_pct > 80:
                            status = "CRITICAL"
                        elif usage_pct > 60:
                            status = "WARNING"
                        elif usage_pct > 40:
                            status = "ELEVATED"
                        else:
                            status = "NORMAL"
                        
                        hosts[instance] = {
                            "total_gb": total_gb,
                            "used_gb": used_gb,
                            "available_gb": available_gb,
                            "usage_pct": usage_pct,
                            "status": status
                        }
                    except (ValueError, TypeError, IndexError) as e:
                        hosts[instance] = {"error": str(e)}
            
            return hosts
        except Exception as e:
            return {"error": str(e)}
    
    def fetch_container_memory(self) -> Dict[str, Any]:
        """Fetch container memory metrics from Prometheus"""
        try:
            # Get container memory usage and limits
            usage_result = self.mcp.prometheus_query('container_memory_usage_bytes{container_name!=""}')
            limit_result = self.mcp.prometheus_query('container_spec_memory_limit_bytes{container_name!=""}')
            
            containers = {}
            
            if usage_result.get('status') == 'success':
                usage_data = usage_result.get('data', {}).get('result', [])
                limit_data = limit_result.get('data', {}).get('result', [])
                
                for result in usage_data:
                    container = result.get('metric', {}).get('container_name', 'unknown')
                    
                    # Skip pause containers
                    if container in ['', 'POD', 'pause'] or not container:
                        continue
                    
                    try:
                        # Get memory usage in bytes
                        memory_bytes = float(result.get('value', [0, 0])[1])
                        memory_mb = memory_bytes / (1024 * 1024)
                        
                        # Find memory limit for this container
                        memory_limit_bytes = next(
                            (float(r.get('value', [0, 0])[1]) for r in limit_data 
                             if r.get('metric', {}).get('container_name') == container),
                            float('inf')
                        )
                        
                        # Handle unlimited containers
                        if memory_limit_bytes == float('inf') or memory_limit_bytes == 0:
                            usage_percent = 0
                            memory_limit_mb = float('inf')
                        else:
                            memory_limit_mb = memory_limit_bytes / (1024 * 1024)
                            usage_percent = (memory_bytes / memory_limit_bytes) * 100
                        
                        # Determine status
                        if usage_percent > 80:
                            status = "CRITICAL"
                        elif usage_percent > 60:
                            status = "WARNING"
                        elif usage_percent > 40:
                            status = "ELEVATED"
                        else:
                            status = "NORMAL"
                        
                        # Store container info
                        containers[container] = {
                            "memory_mb": memory_mb,
                            "limit_mb": memory_limit_mb if memory_limit_mb != float('inf') else None,
                            "usage_percent": usage_percent,
                            "status": status
                        }
                    except (ValueError, TypeError, ZeroDivisionError) as e:
                        containers[container] = {"error": str(e)}
            
            return containers
        except Exception as e:
            return {"error": str(e)}
    
    def fetch_alerts(self) -> List[Dict[str, Any]]:
        """Fetch memory-related alerts from Prometheus"""
        try:
            alerts_result = self.mcp.prometheus_get_alerts()
            
            if alerts_result.get('status') == 'success':
                all_alerts = alerts_result.get('data', {}).get('alerts', [])
                
                # Filter for memory-related alerts
                memory_alerts = [
                    alert for alert in all_alerts 
                    if 'alertname' in alert.get('labels', {}) and 
                    any(term in alert.get('labels', {}).get('alertname', '').lower() 
                        for term in ['memory', 'mem', 'swap', 'container'])
                ]
                
                # Format alerts for display
                formatted_alerts = []
                for alert in memory_alerts:
                    alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
                    severity = alert.get('labels', {}).get('severity', 'unknown')
                    state = alert.get('state', 'unknown')
                    
                    # Get target (container or instance)
                    if 'container' in alert_name.lower() or 'name' in alert.get('labels', {}):
                        target = alert.get('labels', {}).get('name', 
                                 alert.get('labels', {}).get('container_name', 'unknown'))
                        target_type = "container"
                    else:
                        target = alert.get('labels', {}).get('instance', 'unknown')
                        target_type = "host"
                    
                    summary = alert.get('annotations', {}).get('summary', 'No summary available')
                    
                    formatted_alerts.append({
                        "name": alert_name,
                        "severity": severity,
                        "state": state,
                        "target": target,
                        "target_type": target_type,
                        "summary": summary
                    })
                
                return formatted_alerts
            else:
                return [{"error": f"Failed to fetch alerts: {alerts_result.get('error', 'Unknown error')}"}]
        except Exception as e:
            return [{"error": str(e)}]
    
    def update_data(self):
        """Update all dashboard data"""
        self.latest_data["system_memory"] = self.fetch_system_memory()
        self.latest_data["container_memory"] = self.fetch_container_memory()
        self.latest_data["alerts"] = self.fetch_alerts()
        self.latest_data["last_update"] = datetime.now()
    
    def print_dashboard(self):
        """Print the memory dashboard to the console"""
        self.update_data()
        
        print("\n" + "=" * 80)
        print(f"MCP MEMORY DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # System Memory Section
        print("\nSYSTEM MEMORY")
        print("-" * 80)
        
        system_mem = self.latest_data["system_memory"]
        if "error" in system_mem:
            print(f"Error fetching system memory: {system_mem['error']}")
        else:
            for instance, data in system_mem.items():
                if "error" in data:
                    print(f"Host {instance}: Error - {data['error']}")
                    continue
                
                status_color = {
                    "NORMAL": "",
                    "ELEVATED": "",
                    "WARNING": "",
                    "CRITICAL": ""
                }[data["status"]]
                
                print(f"Host: {instance}")
                print(f"  Memory: {data['used_gb']:.2f} GB / {data['total_gb']:.2f} GB ({data['usage_pct']:.1f}%)")
                print(f"  Available: {data['available_gb']:.2f} GB")
                print(f"  Status: {data['status']}")
                print()
        
        # Container Memory Section
        print("\nCONTAINER MEMORY")
        print("-" * 80)
        
        container_mem = self.latest_data["container_memory"]
        if "error" in container_mem:
            print(f"Error fetching container memory: {container_mem['error']}")
        else:
            # Sort containers by usage percentage (highest first)
            sorted_containers = sorted(
                [(name, data) for name, data in container_mem.items() if "error" not in data],
                key=lambda x: x[1]["usage_percent"],
                reverse=True
            )
            
            for container, data in sorted_containers:
                limit_text = f"/ {data['limit_mb']:.2f} MB ({data['usage_percent']:.1f}%)" if data["limit_mb"] else "(no limit)"
                
                print(f"Container: {container}")
                print(f"  Memory: {data['memory_mb']:.2f} MB {limit_text}")
                print(f"  Status: {data['status']}")
                print()
            
            # Print containers with errors
            error_containers = [(name, data) for name, data in container_mem.items() if "error" in data]
            if error_containers:
                print("\nContainers with errors:")
                for container, data in error_containers:
                    print(f"  {container}: {data['error']}")
        
        # Alerts Section
        print("\nACTIVE ALERTS")
        print("-" * 80)
        
        alerts = self.latest_data["alerts"]
        if not alerts:
            print("No memory-related alerts found.")
        elif "error" in alerts[0]:
            print(f"Error fetching alerts: {alerts[0]['error']}")
        else:
            # Filter for active alerts and sort by severity
            active_alerts = [a for a in alerts if a["state"].lower() == "firing"]
            
            severity_order = {"critical": 0, "warning": 1, "info": 2, "unknown": 3}
            sorted_alerts = sorted(
                active_alerts,
                key=lambda x: severity_order.get(x["severity"].lower(), 4)
            )
            
            if not sorted_alerts:
                print("No active memory alerts.")
            else:
                for i, alert in enumerate(sorted_alerts):
                    target_type = "Container" if alert["target_type"] == "container" else "Host"
                    
                    print(f"Alert {i+1}: {alert['name']}")
                    print(f"  {target_type}: {alert['target']}")
                    print(f"  Severity: {alert['severity'].upper()}")
                    print(f"  Summary: {alert['summary']}")
                    print()
        
        print("=" * 80)
        print(f"Last update: {self.latest_data['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"MCP Server: {self.mcp_server_url}")
        print(f"Prometheus: {self.prometheus_url}")
        print("=" * 80)
    
    def run_dashboard(self):
        """Run the dashboard with periodic updates"""
        try:
            while True:
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Update and print dashboard
                self.print_dashboard()
                
                # Wait for next refresh
                print(f"\nRefreshing in {self.refresh_interval} seconds... (Press Ctrl+C to exit)")
                time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            print("\nDashboard stopped.")

def main():
    """Main function to run the dashboard"""
    parser = argparse.ArgumentParser(description="MCP Memory Dashboard")
    parser.add_argument("--mcp-url", default=os.getenv("MCP_SERVER_URL", "http://localhost:8000"),
                        help="MCP server URL")
    parser.add_argument("--prometheus-url", default=os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
                        help="Prometheus server URL")
    parser.add_argument("--refresh", type=int, default=5,
                        help="Dashboard refresh interval in seconds")
    parser.add_argument("--once", action="store_true",
                        help="Print dashboard once and exit")
    
    args = parser.parse_args()
    
    dashboard = MemoryDashboard(
        mcp_server_url=args.mcp_url,
        prometheus_url=args.prometheus_url,
        refresh_interval=args.refresh
    )
    
    if args.once:
        dashboard.print_dashboard()
    else:
        dashboard.run_dashboard()

if __name__ == "__main__":
    main() 