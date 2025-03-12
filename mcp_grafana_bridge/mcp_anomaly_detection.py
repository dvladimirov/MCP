#!/usr/bin/env python3
"""
MCP Anomaly Detection API
Provides API endpoints to integrate Kubernetes performance anomaly detection with MCP
"""

import os
import json
import logging
import threading
import time
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mcp-anomaly-detection')

# Configuration from environment variables
ANOMALY_DETECTION_INTERVAL = int(os.environ.get('ANOMALY_DETECTION_INTERVAL', 300))  # 5 minutes by default
K8S_SCRIPT_PATH = os.environ.get('K8S_SCRIPT_PATH', '/app/scripts/kubernetes_performance_anomalies.py')
PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://prometheus:9090')
DETECTION_ENABLED = os.environ.get('DETECTION_ENABLED', 'true').lower() == 'true'

app = Flask(__name__)

# Store the latest detection results
latest_results = {
    "timestamp": None,
    "results": None,
    "running": False
}

def run_anomaly_detection(node_filter=".*", once=True):
    """Run the anomaly detection script and store results"""
    try:
        latest_results["running"] = True
        logger.info(f"Starting anomaly detection for node filter: {node_filter}")
        
        # Run the script as a subprocess
        cmd = [
            "python3", K8S_SCRIPT_PATH,
            "--prometheus-url", PROMETHEUS_URL,
            "--node", node_filter,
            "--once" if once else ""
        ]
        
        # Filter out empty arguments
        cmd = [arg for arg in cmd if arg]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Anomaly detection failed: {stderr}")
            latest_results["results"] = {
                "error": True,
                "message": stderr,
                "anomalies": {}
            }
        else:
            logger.info("Anomaly detection completed successfully")
            
            # Try to find the latest anomaly JSON file
            anomaly_files = [f for f in os.listdir('.') if f.startswith('kubernetes_anomalies_') and f.endswith('.json')]
            if anomaly_files:
                # Sort by filename (which includes timestamp)
                latest_file = sorted(anomaly_files)[-1]
                with open(latest_file, 'r') as f:
                    latest_results["results"] = json.load(f)
                    logger.info(f"Loaded results from {latest_file}")
            else:
                latest_results["results"] = {
                    "error": False,
                    "message": "No anomalies detected",
                    "anomalies": {}
                }
        
        latest_results["timestamp"] = datetime.now().isoformat()
        latest_results["running"] = False
        
    except Exception as e:
        logger.error(f"Error running anomaly detection: {e}")
        latest_results["results"] = {
            "error": True,
            "message": str(e),
            "anomalies": {}
        }
        latest_results["timestamp"] = datetime.now().isoformat()
        latest_results["running"] = False

def continuous_anomaly_detection():
    """Run anomaly detection continuously in the background"""
    while True:
        try:
            # Only run if not already running
            if not latest_results["running"]:
                run_anomaly_detection(once=True)
            
            # Sleep for the configured interval
            time.sleep(ANOMALY_DETECTION_INTERVAL)
        except Exception as e:
            logger.error(f"Error in continuous anomaly detection: {e}")
            time.sleep(60)  # Sleep for a minute before retrying

# Start the background anomaly detection if enabled
if DETECTION_ENABLED:
    detection_thread = threading.Thread(target=continuous_anomaly_detection, daemon=True)
    detection_thread.start()
    logger.info(f"Started continuous anomaly detection with interval {ANOMALY_DETECTION_INTERVAL} seconds")

@app.route('/api/anomaly/status', methods=['GET'])
def get_anomaly_status():
    """Get the status of the anomaly detection service"""
    return jsonify({
        "service": "kubernetes-anomaly-detection",
        "enabled": DETECTION_ENABLED,
        "running": latest_results["running"],
        "last_run": latest_results["timestamp"],
        "interval": ANOMALY_DETECTION_INTERVAL
    })

@app.route('/api/anomaly/latest', methods=['GET'])
def get_latest_anomalies():
    """Get the latest anomaly detection results"""
    return jsonify({
        "timestamp": latest_results["timestamp"],
        "results": latest_results["results"],
        "running": latest_results["running"]
    })

@app.route('/api/anomaly/run', methods=['POST'])
def trigger_anomaly_detection():
    """Manually trigger anomaly detection"""
    data = request.json or {}
    node_filter = data.get('node_filter', '.*')
    
    # Start detection in a background thread to not block the API response
    detection_thread = threading.Thread(
        target=run_anomaly_detection,
        args=(node_filter, True),
        daemon=True
    )
    detection_thread.start()
    
    return jsonify({
        "status": "started",
        "message": f"Anomaly detection started for node filter: {node_filter}",
        "running": True
    })

@app.route('/api/anomaly/configure', methods=['POST'])
def configure_anomaly_detection():
    """Update the anomaly detection configuration"""
    global ANOMALY_DETECTION_INTERVAL, DETECTION_ENABLED
    
    data = request.json or {}
    
    if 'interval' in data:
        try:
            ANOMALY_DETECTION_INTERVAL = int(data['interval'])
            logger.info(f"Updated detection interval to {ANOMALY_DETECTION_INTERVAL} seconds")
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"Invalid interval value: {e}"}), 400
    
    if 'enabled' in data:
        try:
            DETECTION_ENABLED = bool(data['enabled'])
            logger.info(f"Set detection enabled to {DETECTION_ENABLED}")
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"Invalid enabled value: {e}"}), 400
    
    return jsonify({
        "status": "configured",
        "settings": {
            "interval": ANOMALY_DETECTION_INTERVAL,
            "enabled": DETECTION_ENABLED
        }
    })

# Initialize with empty detection run
if __name__ == '__main__':
    logger.info("MCP Anomaly Detection API starting up")
    app.run(host='0.0.0.0', port=int(os.environ.get('ANOMALY_API_PORT', 8086))) 