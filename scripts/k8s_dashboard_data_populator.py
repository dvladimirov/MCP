#!/usr/bin/env python3
"""
Kubernetes Dashboard Data Populator
This script modifies the Kubernetes dashboard JSON to use the dummy data metrics
"""

import os
import json
import logging
import argparse
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('k8s-dashboard-data-populator')

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DASHBOARD_PATH = os.path.join(PROJECT_ROOT, "grafana", "dashboards", "kubernetes_performance_dashboard.json")
BACKUP_SUFFIX = ".backup"

# Panel titles to update
PANEL_TITLES = {
    "cpu_top": "CPU Top 20 by Pod",
    "memory_top": "Top 20 Memory by Pod",
    "disk_write": "Top 20 Disk I/O Writes by Pod",
    "disk_read": "Top 20 Disk I/O Reads by Pod",
    "iops_write": "Top 20 Disk Write IOPS by Pod",
    "iops_read": "Top 20 Disk Read IOPS by Pod",
    "network_tx": "Top Network Transmit by Pod (with AI Anomaly Detection)",
    "network_errors": "Top 20 Network Transmit Errors by Pod",
    "network_rx_errors": "Top 20 Network Receive Errors by Pod",
}

# Queries to use for each panel
DUMMY_QUERIES = {
    "cpu_top": 'topk(20, rate(container_cpu_usage_seconds_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)',
    "memory_top": 'topk(20, container_memory_usage_bytes{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"})',
    "disk_write": 'topk(20, rate(container_fs_writes_bytes_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)',
    "disk_read": 'topk(20, rate(container_fs_reads_bytes_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)',
    "iops_write": 'topk(10, rate(container_fs_writes_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)',
    "iops_read": 'topk(10, rate(container_fs_reads_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)',
    "network_tx": 'topk(20, rate(container_network_transmit_bytes_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)',
    "network_errors": 'topk(20, rate(container_network_transmit_errors_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)',
    "network_rx_errors": 'topk(20,rate(container_network_receive_errors_total{container_name!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]))'
}

def backup_dashboard():
    """Create a backup of the dashboard JSON"""
    if not os.path.exists(DASHBOARD_PATH):
        logger.error(f"Dashboard file not found at {DASHBOARD_PATH}")
        return False
        
    backup_path = f"{DASHBOARD_PATH}{BACKUP_SUFFIX}"
    try:
        with open(DASHBOARD_PATH, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False

def update_dashboard_panels():
    """Update dashboard panels to use the dummy data metrics"""
    if not os.path.exists(DASHBOARD_PATH):
        logger.error(f"Dashboard file not found at {DASHBOARD_PATH}")
        return False
    
    try:
        # Load the dashboard JSON
        with open(DASHBOARD_PATH, 'r') as f:
            dashboard = json.load(f)
        
        # Track panel updates
        updated_panels = 0
        
        # Process panels
        for panel in dashboard.get('panels', []):
            panel_title = panel.get('title', '')
            
            # Find which type of panel this is
            panel_key = None
            for key, title in PANEL_TITLES.items():
                if title.lower() in panel_title.lower():
                    panel_key = key
                    break
            
            if not panel_key:
                continue
            
            # Update the panel query
            if 'targets' in panel and len(panel['targets']) > 0:
                # Get the original query to preserve structure
                original_expr = panel['targets'][0].get('expr', '')
                
                # If there's an existing query, try to preserve its structure
                if original_expr:
                    # Extract and preserve any template variables like $node_name
                    template_vars = re.findall(r'\$\w+', original_expr)
                    
                    # Start with our dummy query
                    new_expr = DUMMY_QUERIES[panel_key]
                    
                    # Reapply any template variables to preserve dashboard functionality
                    for var in template_vars:
                        # If the variable is in a hostname selector, add it to our query
                        if f'kubernetes_io_hostname=~"{var}"' in original_expr:
                            # Replace simple filter with the template variable filter
                            new_expr = new_expr.replace('pod!=""}', f'pod!="",kubernetes_io_hostname=~"{var}"}}')
                
                    panel['targets'][0]['expr'] = new_expr
                else:
                    # If no existing query, just use our default
                    panel['targets'][0]['expr'] = DUMMY_QUERIES[panel_key]
                
                updated_panels += 1
                logger.info(f"Updated query for panel: {panel_title}")
                
                # Add a note to the panel description
                if 'description' not in panel or not panel['description']:
                    panel['description'] = "Using dummy data from the Kubernetes pod simulator"
                else:
                    # Only add the note if it's not already there
                    if "dummy data" not in panel['description']:
                        panel['description'] += "\n\nUsing dummy data from the Kubernetes pod simulator"
        
        # Save the updated dashboard
        with open(DASHBOARD_PATH, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        logger.info(f"Updated {updated_panels} panels in the dashboard")
        return updated_panels > 0
    
    except Exception as e:
        logger.error(f"Failed to update dashboard: {e}")
        return False

def restore_dashboard_backup():
    """Restore the dashboard from backup"""
    backup_path = f"{DASHBOARD_PATH}{BACKUP_SUFFIX}"
    if not os.path.exists(backup_path):
        logger.error(f"Backup file not found at {backup_path}")
        return False
    
    try:
        with open(backup_path, 'r') as src, open(DASHBOARD_PATH, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Restored dashboard from backup")
        return True
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        return False

def get_dummy_data_script_path():
    """Get the path to the dummy data generator script"""
    script_path = os.path.join(SCRIPT_DIR, "k8s_dummy_data_generator.py")
    if os.path.exists(script_path):
        return script_path
    return None

def add_grafana_datasource_prometheus():
    """Check if there's a provisioning directory and add Prometheus datasource if needed"""
    provisioning_dir = os.path.join(PROJECT_ROOT, "grafana", "provisioning")
    datasources_dir = os.path.join(provisioning_dir, "datasources")
    
    # Create directories if they don't exist
    if not os.path.exists(datasources_dir):
        try:
            os.makedirs(datasources_dir, exist_ok=True)
            logger.info(f"Created datasources directory at {datasources_dir}")
        except Exception as e:
            logger.error(f"Failed to create datasources directory: {e}")
            return False
    
    # Define the Prometheus datasource
    datasource = {
        "apiVersion": 1,
        "datasources": [
            {
                "name": "Prometheus",
                "type": "prometheus",
                "access": "proxy",
                "url": "http://prometheus:9090",
                "isDefault": True,
                "editable": True
            }
        ]
    }
    
    # Write datasource file
    datasource_path = os.path.join(datasources_dir, "prometheus.yaml")
    try:
        with open(datasource_path, 'w') as f:
            yaml_content = "apiVersion: 1\ndatasources:\n"
            yaml_content += "  - name: Prometheus\n"
            yaml_content += "    type: prometheus\n"
            yaml_content += "    access: proxy\n"
            yaml_content += "    url: http://prometheus:9090\n"
            yaml_content += "    isDefault: true\n"
            yaml_content += "    editable: true\n"
            f.write(yaml_content)
        logger.info(f"Created Prometheus datasource at {datasource_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create Prometheus datasource: {e}")
        return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Populate Kubernetes dashboard with dummy data')
    
    parser.add_argument('--update', action='store_true',
                        help='Update the dashboard panels to use dummy data')
    
    parser.add_argument('--restore', action='store_true',
                        help='Restore the dashboard from backup')
    
    parser.add_argument('--add-datasource', action='store_true',
                        help='Add Prometheus datasource to Grafana')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Check for the dummy data generator script
    dummy_script_path = get_dummy_data_script_path()
    if dummy_script_path:
        logger.info(f"Found dummy data generator at {dummy_script_path}")
    else:
        logger.warning("Dummy data generator script not found")
    
    # Add Prometheus datasource
    if args.add_datasource:
        add_grafana_datasource_prometheus()
    
    # Update or restore the dashboard
    if args.restore:
        restore_dashboard_backup()
    elif args.update:
        backup_dashboard()
        update_dashboard_panels()
    else:
        # Default action is to update
        backup_dashboard()
        update_dashboard_panels()
    
    logger.info("Dashboard data populator completed")
    print("\nTo run the dummy data generator:")
    print(f"python3 {os.path.join(SCRIPT_DIR, 'k8s_dummy_data_generator.py')} --http-port 9092")
    print("\nMake sure to restart Grafana after making these changes.")

if __name__ == "__main__":
    main() 