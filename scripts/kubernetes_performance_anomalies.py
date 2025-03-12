#!/usr/bin/env python3
"""
Kubernetes Performance Anomaly Detection
This script analyzes Kubernetes metrics and identifies anomalies in resource utilization
"""

import os
import sys
import json
import time
import logging
import argparse
import statistics
import numpy as np
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("kubernetes_anomalies.log")
    ]
)
logger = logging.getLogger('kubernetes-anomaly-detector')

# Configuration from environment variables
PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://localhost:9090')
ALERT_THRESHOLD_PERCENTAGE = float(os.environ.get('ALERT_THRESHOLD_PERCENTAGE', 90.0))
ANOMALY_DETECTION_WINDOW = os.environ.get('ANOMALY_DETECTION_WINDOW', '30m')
ANOMALY_Z_SCORE_THRESHOLD = float(os.environ.get('ANOMALY_Z_SCORE_THRESHOLD', 3.0))

class KubernetesAnomalyDetector:
    """
    Detects anomalies in Kubernetes performance metrics using various statistical methods
    """
    
    def __init__(self, prometheus_url, alert_threshold=90.0, window='30m', z_score_threshold=3.0):
        """Initialize the anomaly detector with configuration settings"""
        self.prometheus_url = prometheus_url
        self.alert_threshold = alert_threshold
        self.window = window
        self.z_score_threshold = z_score_threshold
        logger.info(f"Initialized Kubernetes Anomaly Detector with Prometheus URL: {prometheus_url}")
        logger.info(f"Alert threshold: {alert_threshold}%, Window: {window}, Z-score threshold: {z_score_threshold}")
    
    def query_prometheus(self, query):
        """Execute a PromQL query and return the results"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return None
    
    def query_prometheus_range(self, query, start_time, end_time, step):
        """Execute a PromQL range query over a time period"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params={
                    "query": query,
                    "start": start_time.timestamp(),
                    "end": end_time.timestamp(),
                    "step": step
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error querying Prometheus range: {e}")
            return None
    
    def detect_z_score_anomalies(self, data_points):
        """
        Detect anomalies using Z-score method
        Returns anomalies and their Z-scores
        """
        if not data_points or len(data_points) < 4:  # Need enough points for meaningful statistics
            return []
            
        values = [float(point[1]) for point in data_points]
        
        # Calculate mean and standard deviation
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Avoid division by zero
        if stdev == 0:
            return []
            
        # Calculate Z-scores and find anomalies
        anomalies = []
        for i, point in enumerate(data_points):
            z_score = (float(point[1]) - mean) / stdev
            if abs(z_score) > self.z_score_threshold:
                anomalies.append({
                    "timestamp": point[0],
                    "value": float(point[1]),
                    "z_score": z_score,
                    "threshold": self.z_score_threshold
                })
                
        return anomalies
    
    def check_cpu_usage_anomalies(self, node_name=".*"):
        """Check for anomalies in CPU usage for pods"""
        query = f"""
        topk(20, rate(container_cpu_usage_seconds_total{{container_name!="POD",container!="",image!="",pod!="",kubernetes_io_hostname=~"{node_name}"}}[5m]) > 0)
        """
        
        # Get current data
        result = self.query_prometheus(query)
        if not result or 'data' not in result or 'result' not in result['data']:
            logger.error("Failed to get CPU usage data")
            return []
            
        anomalies = []
        # Check each pod's CPU usage
        for metric in result['data']['result']:
            pod_name = metric['metric'].get('pod', 'unknown')
            node = metric['metric'].get('kubernetes_io_hostname', 'unknown')
            cpu_usage = float(metric['value'][1])
            
            # Get historical data for this pod for anomaly detection
            pod_query = f"""
            rate(container_cpu_usage_seconds_total{{pod="{pod_name}",kubernetes_io_hostname="{node}"}}[5m])
            """
            
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=30)  # 30 minutes of historical data
            
            range_result = self.query_prometheus_range(pod_query, start_time, end_time, "1m")
            
            if range_result and 'data' in range_result and 'result' in range_result['data'] and range_result['data']['result']:
                data_points = range_result['data']['result'][0]['values']
                z_score_anomalies = self.detect_z_score_anomalies(data_points)
                
                if z_score_anomalies:
                    anomalies.append({
                        "pod": pod_name,
                        "node": node,
                        "metric": "cpu_usage",
                        "current_value": cpu_usage,
                        "anomalies": z_score_anomalies
                    })
                    
                    logger.warning(f"CPU usage anomaly detected for pod {pod_name} on node {node}: {cpu_usage}")
        
        return anomalies
    
    def check_memory_usage_anomalies(self, node_name=".*"):
        """Check for anomalies in memory usage for pods"""
        query = f"""
        topk(20,sum(container_memory_usage_bytes{{pod!="",kubernetes_io_hostname=~"{node_name}"}}) by (pod, kubernetes_io_hostname))
        """
        
        result = self.query_prometheus(query)
        if not result or 'data' not in result or 'result' not in result['data']:
            logger.error("Failed to get memory usage data")
            return []
            
        anomalies = []
        for metric in result['data']['result']:
            pod_name = metric['metric'].get('pod', 'unknown')
            node = metric['metric'].get('kubernetes_io_hostname', 'unknown')
            memory_usage = float(metric['value'][1])
            
            # Get historical data for this pod
            pod_query = f"""
            sum(container_memory_usage_bytes{{pod="{pod_name}",kubernetes_io_hostname="{node}"}})
            """
            
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=30)
            
            range_result = self.query_prometheus_range(pod_query, start_time, end_time, "1m")
            
            if range_result and 'data' in range_result and 'result' in range_result['data'] and range_result['data']['result']:
                data_points = range_result['data']['result'][0]['values']
                z_score_anomalies = self.detect_z_score_anomalies(data_points)
                
                if z_score_anomalies:
                    anomalies.append({
                        "pod": pod_name,
                        "node": node,
                        "metric": "memory_usage",
                        "current_value": memory_usage,
                        "anomalies": z_score_anomalies
                    })
                    
                    logger.warning(f"Memory usage anomaly detected for pod {pod_name} on node {node}: {memory_usage} bytes")
        
        return anomalies
    
    def check_disk_io_anomalies(self, node_name=".*"):
        """Check for anomalies in disk I/O for pods"""
        # Check for write anomalies
        write_query = f"""
        topk(20, sum(rate(container_fs_writes_bytes_total{{pod!="",kubernetes_io_hostname=~"{node_name}"}}[5m])) by (pod,device,kubernetes_io_hostname))
        """
        
        result = self.query_prometheus(write_query)
        if not result or 'data' not in result or 'result' not in result['data']:
            logger.error("Failed to get disk write data")
            return []
            
        anomalies = []
        for metric in result['data']['result']:
            pod_name = metric['metric'].get('pod', 'unknown')
            node = metric['metric'].get('kubernetes_io_hostname', 'unknown')
            device = metric['metric'].get('device', 'unknown')
            io_writes = float(metric['value'][1])
            
            # Get historical data
            pod_query = f"""
            sum(rate(container_fs_writes_bytes_total{{pod="{pod_name}",device="{device}",kubernetes_io_hostname="{node}"}}[5m]))
            """
            
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=30)
            
            range_result = self.query_prometheus_range(pod_query, start_time, end_time, "1m")
            
            if range_result and 'data' in range_result and 'result' in range_result['data'] and range_result['data']['result']:
                data_points = range_result['data']['result'][0]['values']
                z_score_anomalies = self.detect_z_score_anomalies(data_points)
                
                if z_score_anomalies:
                    anomalies.append({
                        "pod": pod_name,
                        "node": node,
                        "device": device,
                        "metric": "disk_writes",
                        "current_value": io_writes,
                        "anomalies": z_score_anomalies
                    })
                    
                    logger.warning(f"Disk write anomaly detected for pod {pod_name} on node {node}, device {device}: {io_writes} B/s")
        
        # Check for read anomalies
        read_query = f"""
        topk(20,sum(rate(container_fs_reads_bytes_total{{pod!="",kubernetes_io_hostname=~"{node_name}"}}[5m])) by (pod,device,kubernetes_io_hostname))
        """
        
        result = self.query_prometheus(read_query)
        if not result or 'data' not in result or 'result' not in result['data']:
            logger.error("Failed to get disk read data")
            return anomalies  # Return write anomalies only
            
        for metric in result['data']['result']:
            pod_name = metric['metric'].get('pod', 'unknown')
            node = metric['metric'].get('kubernetes_io_hostname', 'unknown')
            device = metric['metric'].get('device', 'unknown')
            io_reads = float(metric['value'][1])
            
            # Get historical data
            pod_query = f"""
            sum(rate(container_fs_reads_bytes_total{{pod="{pod_name}",device="{device}",kubernetes_io_hostname="{node}"}}[5m]))
            """
            
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=30)
            
            range_result = self.query_prometheus_range(pod_query, start_time, end_time, "1m")
            
            if range_result and 'data' in range_result and 'result' in range_result['data'] and range_result['data']['result']:
                data_points = range_result['data']['result'][0]['values']
                z_score_anomalies = self.detect_z_score_anomalies(data_points)
                
                if z_score_anomalies:
                    anomalies.append({
                        "pod": pod_name,
                        "node": node,
                        "device": device,
                        "metric": "disk_reads",
                        "current_value": io_reads,
                        "anomalies": z_score_anomalies
                    })
                    
                    logger.warning(f"Disk read anomaly detected for pod {pod_name} on node {node}, device {device}: {io_reads} B/s")
        
        return anomalies
    
    def check_network_anomalies(self, node_name=".*"):
        """Check for anomalies in network traffic for pods"""
        # Check network transmit anomalies
        tx_query = f"""
        topk(20,rate(container_network_transmit_bytes_total{{name!="",pod!="",kubernetes_io_hostname=~"{node_name}"}}[5m]))
        """
        
        result = self.query_prometheus(tx_query)
        if not result or 'data' not in result or 'result' not in result['data']:
            logger.error("Failed to get network transmit data")
            return []
            
        anomalies = []
        for metric in result['data']['result']:
            pod_name = metric['metric'].get('pod', 'unknown')
            node = metric['metric'].get('kubernetes_io_hostname', 'unknown')
            tx_bytes = float(metric['value'][1])
            
            # Get historical data
            pod_query = f"""
            rate(container_network_transmit_bytes_total{{pod="{pod_name}",kubernetes_io_hostname="{node}"}}[5m])
            """
            
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=30)
            
            range_result = self.query_prometheus_range(pod_query, start_time, end_time, "1m")
            
            if range_result and 'data' in range_result and 'result' in range_result['data'] and range_result['data']['result']:
                data_points = range_result['data']['result'][0]['values']
                z_score_anomalies = self.detect_z_score_anomalies(data_points)
                
                if z_score_anomalies:
                    anomalies.append({
                        "pod": pod_name,
                        "node": node,
                        "metric": "network_transmit",
                        "current_value": tx_bytes,
                        "anomalies": z_score_anomalies
                    })
                    
                    logger.warning(f"Network transmit anomaly detected for pod {pod_name} on node {node}: {tx_bytes} B/s")
        
        # Check network receive anomalies
        rx_query = f"""
        topk(20,rate(container_network_receive_bytes_total{{name!="",pod!="",kubernetes_io_hostname=~"{node_name}"}}[5m]))
        """
        
        result = self.query_prometheus(rx_query)
        if not result or 'data' not in result or 'result' not in result['data']:
            logger.error("Failed to get network receive data")
            return anomalies  # Return transmit anomalies only
            
        for metric in result['data']['result']:
            pod_name = metric['metric'].get('pod', 'unknown')
            node = metric['metric'].get('kubernetes_io_hostname', 'unknown')
            rx_bytes = float(metric['value'][1])
            
            # Get historical data
            pod_query = f"""
            rate(container_network_receive_bytes_total{{pod="{pod_name}",kubernetes_io_hostname="{node}"}}[5m])
            """
            
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=30)
            
            range_result = self.query_prometheus_range(pod_query, start_time, end_time, "1m")
            
            if range_result and 'data' in range_result and 'result' in range_result['data'] and range_result['data']['result']:
                data_points = range_result['data']['result'][0]['values']
                z_score_anomalies = self.detect_z_score_anomalies(data_points)
                
                if z_score_anomalies:
                    anomalies.append({
                        "pod": pod_name,
                        "node": node,
                        "metric": "network_receive",
                        "current_value": rx_bytes,
                        "anomalies": z_score_anomalies
                    })
                    
                    logger.warning(f"Network receive anomaly detected for pod {pod_name} on node {node}: {rx_bytes} B/s")
        
        # Check network errors
        err_tx_query = f"""
        topk(20,rate(container_network_transmit_errors_total{{name!="",pod!="",kubernetes_io_hostname=~"{node_name}"}}[5m]))
        """
        
        result = self.query_prometheus(err_tx_query)
        if result and 'data' in result and 'result' in result['data']:
            for metric in result['data']['result']:
                pod_name = metric['metric'].get('pod', 'unknown')
                node = metric['metric'].get('kubernetes_io_hostname', 'unknown')
                tx_errors = float(metric['value'][1])
                
                # Any non-zero error rate is an anomaly
                if tx_errors > 0:
                    anomalies.append({
                        "pod": pod_name,
                        "node": node,
                        "metric": "network_transmit_errors",
                        "current_value": tx_errors,
                        "anomalies": [{
                            "timestamp": metric['value'][0],
                            "value": tx_errors,
                            "threshold": 0
                        }]
                    })
                    
                    logger.warning(f"Network transmit errors detected for pod {pod_name} on node {node}: {tx_errors} errors/s")
        
        err_rx_query = f"""
        topk(20,rate(container_network_receive_errors_total{{name!="",pod!="",kubernetes_io_hostname=~"{node_name}"}}[5m]))
        """
        
        result = self.query_prometheus(err_rx_query)
        if result and 'data' in result and 'result' in result['data']:
            for metric in result['data']['result']:
                pod_name = metric['metric'].get('pod', 'unknown')
                node = metric['metric'].get('kubernetes_io_hostname', 'unknown')
                rx_errors = float(metric['value'][1])
                
                # Any non-zero error rate is an anomaly
                if rx_errors > 0:
                    anomalies.append({
                        "pod": pod_name,
                        "node": node,
                        "metric": "network_receive_errors",
                        "current_value": rx_errors,
                        "anomalies": [{
                            "timestamp": metric['value'][0],
                            "value": rx_errors,
                            "threshold": 0
                        }]
                    })
                    
                    logger.warning(f"Network receive errors detected for pod {pod_name} on node {node}: {rx_errors} errors/s")
        
        return anomalies
    
    def run_complete_anomaly_detection(self, node_name=".*"):
        """Run a complete anomaly detection across all metric types"""
        all_anomalies = {
            "timestamp": datetime.now().isoformat(),
            "anomalies": {
                "cpu": self.check_cpu_usage_anomalies(node_name),
                "memory": self.check_memory_usage_anomalies(node_name),
                "disk_io": self.check_disk_io_anomalies(node_name),
                "network": self.check_network_anomalies(node_name)
            }
        }
        
        # Count total anomalies
        total_anomalies = (
            len(all_anomalies["anomalies"]["cpu"]) +
            len(all_anomalies["anomalies"]["memory"]) +
            len(all_anomalies["anomalies"]["disk_io"]) +
            len(all_anomalies["anomalies"]["network"])
        )
        
        all_anomalies["total_anomalies"] = total_anomalies
        
        if total_anomalies > 0:
            logger.warning(f"Detected {total_anomalies} anomalies across all metrics")
            
            # Save anomalies to a log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"kubernetes_anomalies_{timestamp}.json", "w") as f:
                json.dump(all_anomalies, f, indent=2)
        else:
            logger.info("No anomalies detected")
        
        return all_anomalies

def main():
    """Main entry point for the anomaly detector"""
    parser = argparse.ArgumentParser(description='Kubernetes Performance Anomaly Detection')
    parser.add_argument('--prometheus-url', default=PROMETHEUS_URL, help='Prometheus server URL')
    parser.add_argument('--threshold', type=float, default=ALERT_THRESHOLD_PERCENTAGE, help='Alert threshold percentage')
    parser.add_argument('--window', default=ANOMALY_DETECTION_WINDOW, help='Time window for analysis')
    parser.add_argument('--z-score', type=float, default=ANOMALY_Z_SCORE_THRESHOLD, help='Z-score threshold for anomalies')
    parser.add_argument('--node', default=".*", help='Regular expression to filter by node name')
    parser.add_argument('--interval', type=int, default=60, help='Run detection every N seconds')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    
    args = parser.parse_args()
    
    detector = KubernetesAnomalyDetector(
        prometheus_url=args.prometheus_url,
        alert_threshold=args.threshold,
        window=args.window,
        z_score_threshold=args.z_score
    )
    
    if args.once:
        detector.run_complete_anomaly_detection(args.node)
    else:
        try:
            while True:
                logger.info(f"Running anomaly detection (node filter: {args.node})")
                detector.run_complete_anomaly_detection(args.node)
                logger.info(f"Sleeping for {args.interval} seconds")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Anomaly detection stopped by user")

if __name__ == "__main__":
    main() 