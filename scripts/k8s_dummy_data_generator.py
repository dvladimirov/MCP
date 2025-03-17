#!/usr/bin/env python3
"""
Simple Kubernetes Metrics Generator for Grafana
-----------------------------------------------
This script directly generates the exact metrics needed for the Kubernetes dashboard queries.

IMPORTANT: This generator has been specifically designed to output metrics that exactly match
the Prometheus Query Language (PQL) queries in the Kubernetes performance dashboard:

1. CPU metrics:
   - Metric: container_cpu_usage_seconds_total
   - Query: topk(20, rate(container_cpu_usage_seconds_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)

2. Memory metrics:
   - Metric: container_memory_usage_bytes
   - Query: topk(20, container_memory_usage_bytes{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"})

3. Disk I/O Write metrics:
   - Metric: container_fs_writes_bytes_total
   - Query: topk(20, rate(container_fs_writes_bytes_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)

4. Disk I/O Read metrics:
   - Metric: container_fs_reads_bytes_total
   - Query: topk(20, rate(container_fs_reads_bytes_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)

5. Disk Read IOPS metrics:
   - Metric: container_fs_reads_total
   - Query: topk(10, rate(container_fs_reads_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)

6. Disk Write IOPS metrics:
   - Metric: container_fs_writes_total
   - Query: topk(10, rate(container_fs_writes_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)

7. Network Transmit metrics:
   - Metric: container_network_transmit_bytes_total
   - Query: topk(20, rate(container_network_transmit_bytes_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)

8. Network Transmit Error metrics:
   - Metric: container_network_transmit_errors_total
   - Query: topk(20, rate(container_network_transmit_errors_total{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]) > 0)

9. Network Receive Error metrics:
   - Metric: container_network_receive_errors_total
   - Query: topk(20, rate(container_network_receive_errors_total{container_name!="",pod!="",kubernetes_io_hostname=~"$node_name"}[5m]))

All metrics include the kubernetes_io_hostname label which is used for node filtering in the dashboard.
"""

import os
import time
import random
import logging
import argparse
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('k8s-metrics-generator')

# Default configuration
DEFAULT_POD_COUNT = 25
HTTP_PORT = 9092
UPDATE_INTERVAL = 15  # seconds

# Node names to use
NODE_NAMES = ["worker-1", "worker-2", "master-1"]

# Pod templates for realistic workloads
POD_TEMPLATES = [
    {"name": "nginx", "container": "nginx-container", "image": "nginx:latest"},
    {"name": "postgres", "container": "postgres-container", "image": "postgres:13"},
    {"name": "redis", "container": "redis-container", "image": "redis:6"},
    {"name": "elasticsearch", "container": "es-container", "image": "elasticsearch:7.13.0"},
    {"name": "prometheus", "container": "prom-container", "image": "prom/prometheus:v2.30.0"},
    {"name": "grafana", "container": "grafana-container", "image": "grafana/grafana:latest"},
    {"name": "mongodb", "container": "mongo-container", "image": "mongo:4.4"},
    {"name": "kafka", "container": "kafka-container", "image": "confluentinc/cp-kafka:latest"},
    {"name": "mysql", "container": "mysql-container", "image": "mysql:8"},
    {"name": "rabbitmq", "container": "rabbitmq-container", "image": "rabbitmq:3.9"},
]

class MetricsGenerator:
    """Generates Kubernetes metrics in Prometheus format"""

    def __init__(self, pod_count=DEFAULT_POD_COUNT):
        self.pod_count = pod_count
        self.pods = []
        self.running = False
        self.initialize_pods()

    def initialize_pods(self):
        """Create simulated pods with unique names"""
        logger.info(f"Initializing {self.pod_count} pods...")
        
        for i in range(self.pod_count):
            # Select a random template
            template = random.choice(POD_TEMPLATES)
            
            # Generate a unique pod name
            pod_name = f"{template['name']}-{random.randint(1000, 9999)}"
            
            # Assign to a random node
            node_name = random.choice(NODE_NAMES)
            
            # Create the pod entry
            pod = {
                "name": pod_name,
                "container_name": template["container"],
                "image": template["image"],
                "node": node_name,
                "namespace": "default",
                "uid": f"docker-{pod_name}-{random.randint(100000, 999999)}"
            }
            
            self.pods.append(pod)
        
        logger.info(f"Initialized {len(self.pods)} pods")

    def generate_metrics(self):
        """Generate metrics for all pods"""
        metrics = []
        timestamp = time.time()
        
        for pod in self.pods:
            # Generate common labels for this pod
            common_labels = (
                f'{{container_name="{pod["container_name"]}",'
                f'container="{pod["container_name"]}",'
                f'id="/docker/{pod["uid"]}",'
                f'image="{pod["image"]}",'
                f'name="{pod["name"]}",'
                f'namespace="{pod["namespace"]}",'
                f'pod="{pod["name"]}",'
                f'kubernetes_io_hostname="{pod["node"]}"}}'
            )
            
            # 1. CPU metrics (needed for Top 20 CPU panel)
            cpu_usage = random.uniform(0.1, 0.9)  # CPU usage between 10% and 90%
            metrics.append(f'container_cpu_usage_seconds_total{common_labels} {cpu_usage * timestamp}')
            
            # 2. Memory metrics (needed for Top 20 Memory panel)
            memory_usage = random.randint(100000000, 2000000000)  # Memory between 100MB and 2GB
            metrics.append(f'container_memory_usage_bytes{common_labels} {memory_usage}')
            
            # 3. Disk I/O metrics
            disk_read_bytes = random.randint(10000, 5000000)  # Between 10KB and 5MB
            disk_write_bytes = random.randint(5000, 2000000)  # Between 5KB and 2MB
            disk_labels = common_labels[:-1] + ',device="pod"' + common_labels[-1:]
            
            metrics.append(f'container_fs_reads_bytes_total{disk_labels} {disk_read_bytes * timestamp}')
            metrics.append(f'container_fs_writes_bytes_total{disk_labels} {disk_write_bytes * timestamp}')
            
            # 4. IOPS metrics (reads and writes count)
            iops_read = disk_read_bytes / 4096  # Approximate IOPS based on 4KB blocks
            iops_write = disk_write_bytes / 4096
            metrics.append(f'container_fs_reads_total{disk_labels} {iops_read * timestamp}')
            metrics.append(f'container_fs_writes_total{disk_labels} {iops_write * timestamp}')
            
            # 5. Network metrics (transmit and receive)
            net_labels = common_labels[:-1] + ',interface="eth0"' + common_labels[-1:]
            tx_bytes = random.randint(50000, 10000000)  # Between 50KB and 10MB
            rx_bytes = random.randint(100000, 20000000)  # Between 100KB and 20MB
            
            metrics.append(f'container_network_transmit_bytes_total{net_labels} {tx_bytes * timestamp}')
            metrics.append(f'container_network_receive_bytes_total{net_labels} {rx_bytes * timestamp}')
            
            # 6. Network error metrics
            # Error rates are much lower than normal traffic
            tx_errors = random.randint(0, 10)  # 0-10 errors
            rx_errors = random.randint(0, 15)  # 0-15 errors
            metrics.append(f'container_network_transmit_errors_total{net_labels} {tx_errors * timestamp}')
            metrics.append(f'container_network_receive_errors_total{net_labels} {rx_errors * timestamp}')
        
        return "\n".join(metrics)

class MetricsServer(BaseHTTPRequestHandler):
    """Simple HTTP server to expose metrics in Prometheus format"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/metrics':
            # Generate and return metrics
            metrics = self.server.metrics_generator.generate_metrics()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(metrics.encode('utf-8'))
            logger.debug("Metrics served")
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')

def start_server(port, metrics_generator):
    """Start the HTTP server"""
    # Note: Using 0.0.0.0 to make the service accessible from Docker containers
    # For production environments with security concerns, consider:
    # 1. Using Docker host networking mode to access localhost services
    # 2. Setting up a reverse proxy with authentication
    # 3. Using network isolation with Docker user-defined networks
    server = HTTPServer(('0.0.0.0', port), MetricsServer)
    server.metrics_generator = metrics_generator
    logger.info(f"Starting metrics server on port {port}")
    server.serve_forever()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Generate Kubernetes metrics for Grafana')
    
    parser.add_argument('--pods', type=int, default=DEFAULT_POD_COUNT,
                        help=f'Number of pods to simulate (default: {DEFAULT_POD_COUNT})')
    
    parser.add_argument('--http-port', type=int, default=HTTP_PORT,
                        help=f'HTTP port for the metrics server (default: {HTTP_PORT})')
    
    parser.add_argument('--interval', type=int, default=UPDATE_INTERVAL,
                        help=f'Update interval in seconds (default: {UPDATE_INTERVAL})')
    
    parser.add_argument('--anomalies', action='store_true',
                        help='Generate occasional anomalies (not currently used)')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    logger.info("Starting Kubernetes metrics generator")
    logger.info(f"Generating metrics for {args.pods} pods")
    logger.info(f"HTTP server port: {args.http_port}")
    logger.info(f"Update interval: {args.interval} seconds")
    
    # Create the metrics generator
    metrics_generator = MetricsGenerator(pod_count=args.pods)
    
    # Start the HTTP server in a separate thread
    server_thread = threading.Thread(
        target=start_server,
        args=(args.http_port, metrics_generator),
        daemon=True
    )
    server_thread.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping metrics generator")
        return 0

if __name__ == "__main__":
    main() 