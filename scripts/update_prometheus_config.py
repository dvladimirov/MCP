#!/usr/bin/env python3
"""
Update Prometheus Configuration
Adds a job for scraping the Kubernetes dummy data generator
"""

import os
import sys
import yaml
import socket
import logging
import platform
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('update-prometheus-config')

# File paths
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = SCRIPT_DIR.parent
PROMETHEUS_CONFIG = PROJECT_ROOT / "prometheus" / "prometheus.yml"
BACKUP_SUFFIX = ".bak"

def get_host_ip():
    """Get the IP address to use for host connection from Docker containers"""
    system = platform.system()
    if system == "Darwin" or system == "Windows":
        # macOS and Windows Docker Desktop uses host.docker.internal
        return "host.docker.internal"
    else:
        # On Linux, we need to use the host's actual IP
        # This gets the IP address of the host that can be accessed from a container
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't need to be reachable, just need to set the socket
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '172.17.0.1'  # Docker default bridge network
        finally:
            s.close()
        return ip

def backup_config():
    """Create a backup of the Prometheus config"""
    if not PROMETHEUS_CONFIG.exists():
        logger.error(f"Prometheus config not found at {PROMETHEUS_CONFIG}")
        return False
    
    backup_path = f"{PROMETHEUS_CONFIG}{BACKUP_SUFFIX}"
    try:
        with open(PROMETHEUS_CONFIG, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False

def update_prometheus_config(port=9092):
    """Update the Prometheus config to include the Kubernetes dummy data job"""
    if not PROMETHEUS_CONFIG.exists():
        logger.error(f"Prometheus config not found at {PROMETHEUS_CONFIG}")
        return False
    
    try:
        # Get the host IP for Docker to connect to
        host_ip = get_host_ip()
        logger.info(f"Using host IP: {host_ip} for Prometheus to connect to the metrics generator")
        
        # Read the current config
        with open(PROMETHEUS_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check if the config is valid
        if not config or not isinstance(config, dict):
            logger.error("Invalid Prometheus config format")
            return False
        
        # Ensure scrape_configs exists
        if 'scrape_configs' not in config:
            config['scrape_configs'] = []
        
        # Check if k8s-dummy-data job already exists
        k8s_dummy_job_exists = False
        for job in config['scrape_configs']:
            if job.get('job_name') == 'k8s-dummy-data':
                k8s_dummy_job_exists = True
                # Use the appropriate host IP to connect from Docker to host
                job['static_configs'] = [{'targets': [f'{host_ip}:{port}']}]
                logger.info(f"Updated existing k8s-dummy-data job to use port {port}")
                break
        
        # Add the job if it doesn't exist
        if not k8s_dummy_job_exists:
            k8s_dummy_job = {
                'job_name': 'k8s-dummy-data',
                'static_configs': [{'targets': [f'{host_ip}:{port}']}],
                'scrape_interval': '5s'
            }
            config['scrape_configs'].append(k8s_dummy_job)
            logger.info(f"Added k8s-dummy-data job with port {port}")
        
        # Write the updated config
        with open(PROMETHEUS_CONFIG, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Updated Prometheus config at {PROMETHEUS_CONFIG}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to update Prometheus config: {e}")
        return False

def restore_config():
    """Restore the Prometheus config from backup"""
    backup_path = f"{PROMETHEUS_CONFIG}{BACKUP_SUFFIX}"
    if not os.path.exists(backup_path):
        logger.error(f"Backup file not found at {backup_path}")
        return False
    
    try:
        with open(backup_path, 'r') as src, open(PROMETHEUS_CONFIG, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Restored Prometheus config from backup")
        return True
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update Prometheus config for Kubernetes dummy data')
    parser.add_argument('--port', type=int, default=9092, help='HTTP port for the dummy data generator')
    parser.add_argument('--restore', action='store_true', help='Restore the config from backup')
    
    args = parser.parse_args()
    
    if args.restore:
        success = restore_config()
    else:
        # Create backup first
        backup_config()
        success = update_prometheus_config(args.port)
    
    if success:
        logger.info("Operation completed successfully")
        print("You may need to restart Prometheus for changes to take effect:")
        print("  docker compose restart prometheus")
        return 0
    else:
        logger.error("Operation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 