#!/usr/bin/env python3
"""
Update Kubernetes Performance Dashboard with Dummy Data
This script updates the Kubernetes Performance Dashboard queries to show simulated pods
"""

import os
import json
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('update-k8s-dashboard')

# File paths
DASHBOARD_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           "grafana", "dashboards", "kubernetes_performance_dashboard.json")

# Simulated pod names that should appear in the dashboard
SIMULATED_PODS = [
    "nginx-deployment-66b6c48dd5-abcd1",
    "batch-job-12345-abcde",
    "redis-master-0",
    "postgres-0"
]

def update_dashboard():
    """Update the dashboard JSON with queries that will show simulated pods"""
    try:
        with open(DASHBOARD_PATH, 'r') as f:
            dashboard = json.load(f)
        
        # Find the panel positions
        panel_titles = {
            "cpu": "Top 20 CPU Usage by Pod",
            "memory": "Top 20 Memory Usage by Pod",
            "disk_write": "Top 20 Disk Write by Pod",
            "disk_read": "Top 20 Disk Read by Pod",
            "network_tx": "Top 20 Network Transmit by Pod",
            "network_rx": "Top 20 Network Receive by Pod"
        }
        
        # Create a regex pattern for the simulated pods
        pod_pattern = '|'.join(SIMULATED_PODS)
        
        # Find panels and update them
        updated_panels = 0
        
        for panel in dashboard['panels']:
            title = panel.get('title', '')
            
            # Update CPU panel
            if title == panel_titles["cpu"] or "Top CPU Usage by Pod" in title:
                logger.info(f"Updating panel: {title}")
                
                # Update query to highlight simulated pods
                if 'targets' in panel and panel['targets']:
                    # Update the existing query to ensure our simulated pods appear
                    panel['targets'][0]['expr'] = f"""
                    sum(rate(container_cpu_usage_seconds_total{{container_name!="POD",container!="",image!="",pod=~"({pod_pattern})"}}[5m])) by (pod) * 100 or
                    topk(10, sum(rate(container_cpu_usage_seconds_total{{container_name!="POD",container!="",image!="",pod!=""}}[5m])) by (pod) * 100)
                    """
                    
                updated_panels += 1
            
            # Update Memory panel
            elif title == panel_titles["memory"] or "Top Memory Usage by Pod" in title:
                logger.info(f"Updating panel: {title}")
                
                # Update query to highlight simulated pods
                if 'targets' in panel and panel['targets']:
                    # Update the existing query to ensure our simulated pods appear
                    panel['targets'][0]['expr'] = f"""
                    sum(container_memory_usage_bytes{{pod=~"({pod_pattern})"}}) by (pod) or
                    topk(10, sum(container_memory_usage_bytes{{pod!=""}}) by (pod))
                    """
                
                updated_panels += 1
            
            # Update Disk Write panel
            elif title == panel_titles["disk_write"] or "Top Disk Write by Pod" in title:
                logger.info(f"Updating panel: {title}")
                
                # Update query to highlight simulated pods
                if 'targets' in panel and panel['targets']:
                    # Update the existing query to ensure our simulated pods appear
                    panel['targets'][0]['expr'] = f"""
                    sum(rate(container_fs_writes_bytes_total{{pod=~"({pod_pattern})"}}[5m])) by (pod,device) or
                    topk(10, sum(rate(container_fs_writes_bytes_total{{pod!=""}}[5m])) by (pod,device))
                    """
                
                updated_panels += 1
            
            # Update Disk Read panel
            elif title == panel_titles["disk_read"] or "Top Disk Read by Pod" in title:
                logger.info(f"Updating panel: {title}")
                
                # Update query to highlight simulated pods
                if 'targets' in panel and panel['targets']:
                    # Update the existing query to ensure our simulated pods appear
                    panel['targets'][0]['expr'] = f"""
                    sum(rate(container_fs_reads_bytes_total{{pod=~"({pod_pattern})"}}[5m])) by (pod,device) or
                    topk(10, sum(rate(container_fs_reads_bytes_total{{pod!=""}}[5m])) by (pod,device))
                    """
                
                updated_panels += 1
            
            # Update Network Transmit panel
            elif title == panel_titles["network_tx"] or "Top Network Transmit by Pod" in title:
                logger.info(f"Updating panel: {title}")
                
                # Update query to highlight simulated pods
                if 'targets' in panel and panel['targets']:
                    # Update the existing query to ensure our simulated pods appear
                    panel['targets'][0]['expr'] = f"""
                    sum(rate(container_network_transmit_bytes_total{{pod=~"({pod_pattern})",name!=""}}[5m])) by (pod) or
                    topk(10, sum(rate(container_network_transmit_bytes_total{{name!="",pod!=""}}[5m])) by (pod))
                    """
                
                updated_panels += 1
            
            # Update Network Receive panel
            elif title == panel_titles["network_rx"] or "Top Network Receive by Pod" in title:
                logger.info(f"Updating panel: {title}")
                
                # Update query to highlight simulated pods
                if 'targets' in panel and panel['targets']:
                    # Update the existing query to ensure our simulated pods appear
                    panel['targets'][0]['expr'] = f"""
                    sum(rate(container_network_receive_bytes_total{{pod=~"({pod_pattern})",name!=""}}[5m])) by (pod) or
                    topk(10, sum(rate(container_network_receive_bytes_total{{name!="",pod!=""}}[5m])) by (pod))
                    """
                
                updated_panels += 1
        
        # Update dashboard
        with open(DASHBOARD_PATH, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        logger.info(f"Updated dashboard at {DASHBOARD_PATH} with {updated_panels} modified panels")
        return True
    
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        return False

def main():
    """Main entry point"""
    global DASHBOARD_PATH

    parser = argparse.ArgumentParser(description='Update Kubernetes Performance Dashboard with dummy data')
    parser.add_argument('--dashboard-path', type=str, default=DASHBOARD_PATH,
                        help='Path to the dashboard JSON file')
    
    args = parser.parse_args()
    
    if args.dashboard_path:
        DASHBOARD_PATH = args.dashboard_path
    
    # Update dashboard
    if update_dashboard():
        print(f"✅ Successfully updated dashboard with queries that will show simulated pods")
        print(f"   Dashboard file: {DASHBOARD_PATH}")
        print(f"   Simulated pods: {', '.join(SIMULATED_PODS)}")
        return True
    else:
        print(f"❌ Failed to update dashboard")
        return False

if __name__ == "__main__":
    if main():
        exit(0)
    else:
        exit(1) 