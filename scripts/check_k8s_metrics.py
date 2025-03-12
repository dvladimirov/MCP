#!/usr/bin/env python3
"""
Check Kubernetes Metrics Integration

This script verifies that Prometheus can access the dummy metrics
and that the data is being correctly scraped and stored.
"""

import os
import sys
import json
import logging
import argparse
import requests
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('check-k8s-metrics')

# Default configuration
METRICS_PORT = 9092
PROMETHEUS_URL = "http://localhost:9090"

def check_metrics_endpoint(port):
    """Check if the metrics endpoint is accessible"""
    url = f"http://localhost:{port}/metrics"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            metrics_count = len(response.text.split('\n'))
            logger.info(f"✅ Metrics endpoint is UP - {metrics_count} metrics available")
            return True, metrics_count
        else:
            logger.error(f"❌ Metrics endpoint returned status code {response.status_code}")
            return False, 0
    except Exception as e:
        logger.error(f"❌ Failed to access metrics endpoint: {e}")
        return False, 0

def check_prometheus_connection(prometheus_url):
    """Check if Prometheus is accessible"""
    try:
        response = requests.get(f"{prometheus_url}/api/v1/status/config", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Prometheus is UP and accessible")
            return True
        else:
            logger.error(f"❌ Failed to access Prometheus: Status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to access Prometheus: {e}")
        return False

def check_prometheus_targets(prometheus_url):
    """Check if Prometheus has targets configured"""
    try:
        response = requests.get(f"{prometheus_url}/api/v1/targets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            targets = data.get('data', {}).get('activeTargets', [])
            
            metrics_target = None
            for target in targets:
                if 'localhost:9092' in str(target.get('scrapeUrl', '')):
                    metrics_target = target
                    break
            
            if metrics_target:
                if metrics_target.get('health') == 'up':
                    logger.info(f"✅ Metrics target is configured and UP")
                    return True
                else:
                    logger.error(f"❌ Metrics target is configured but health is {metrics_target.get('health')}")
                    error_msg = metrics_target.get('lastError', 'No error message')
                    if error_msg:
                        logger.error(f"   Error: {error_msg}")
                    return False
            else:
                logger.warning("⚠️ No metrics target found for localhost:9092")
                logger.info("You may need to add a scrape configuration to Prometheus")
                
                # Print a helpful snippet
                logger.info("\nAdd this to your Prometheus config:")
                logger.info("""
  - job_name: 'kubernetes-dummy-metrics'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:9092']
                """)
                
                return False
        else:
            logger.error(f"❌ Failed to get Prometheus targets: Status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to get Prometheus targets: {e}")
        return False

def check_metric_data(prometheus_url, metric_name="container_cpu_usage_seconds_total"):
    """Check if Prometheus has data for a specific metric"""
    try:
        # Query for the metric
        response = requests.get(
            f"{prometheus_url}/api/v1/query",
            params={"query": metric_name},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', {}).get('result', [])
            
            if results:
                logger.info(f"✅ Found {len(results)} series for metric '{metric_name}'")
                
                # Show a sample of the data
                if len(results) > 0:
                    sample = results[0]
                    metric_labels = sample.get('metric', {})
                    # Remove the metric name from the dict to make it cleaner
                    if '__name__' in metric_labels:
                        del metric_labels['__name__']
                    
                    value = sample.get('value', [0, "0"])[1]
                    logger.info(f"   Sample value: {value}")
                    logger.info(f"   Sample labels: {json.dumps(metric_labels, indent=2)}")
                
                return True
            else:
                logger.warning(f"⚠️ No data found for metric '{metric_name}'")
                return False
        else:
            logger.error(f"❌ Failed to query Prometheus: Status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to query Prometheus: {e}")
        return False

def suggest_fixes(metrics_ok, prometheus_ok, targets_ok, data_ok):
    """Suggest fixes based on the check results"""
    if not metrics_ok:
        logger.info("\n🛠️ Suggestions to fix metrics endpoint:")
        logger.info("1. Check if the k8s_dummy_data_generator.py script is running")
        logger.info("2. Verify the port (default: 9092) is correct and not in use")
        logger.info("3. Run the generator script: uv run scripts/k8s_dummy_data_generator.py --http-port 9092")
    
    if not prometheus_ok:
        logger.info("\n🛠️ Suggestions to fix Prometheus connection:")
        logger.info("1. Check if Prometheus is running (docker ps | grep prometheus)")
        logger.info("2. Start Prometheus if it's not running: docker compose up -d prometheus")
        logger.info("3. Verify PROMETHEUS_URL is correct (default: http://localhost:9090)")
    
    if metrics_ok and prometheus_ok and not targets_ok:
        logger.info("\n🛠️ Suggestions to fix Prometheus target configuration:")
        logger.info("1. Add a scrape configuration for the metrics endpoint (see above snippet)")
        logger.info("2. Restart Prometheus: docker compose restart prometheus")
    
    if metrics_ok and prometheus_ok and targets_ok and not data_ok:
        logger.info("\n🛠️ Suggestions to fix missing metric data:")
        logger.info("1. Wait a few minutes for Prometheus to scrape the data")
        logger.info("2. Check if the metrics names in the dashboard match what's being generated")
        logger.info("3. Verify the metric labels match what's expected in the queries")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Check Kubernetes Metrics Integration')
    
    parser.add_argument('--port', type=int, default=METRICS_PORT,
                        help=f'Port where metrics are exposed (default: {METRICS_PORT})')
    
    parser.add_argument('--prometheus', type=str, default=PROMETHEUS_URL,
                        help=f'Prometheus URL (default: {PROMETHEUS_URL})')
    
    parser.add_argument('--metric', type=str, default="container_cpu_usage_seconds_total",
                        help='Metric name to check (default: container_cpu_usage_seconds_total)')
    
    args = parser.parse_args()
    
    # Use local prometheus_url variable instead of global
    prometheus_url = args.prometheus
    
    logger.info("=== Kubernetes Metrics Integration Check ===")
    logger.info(f"Metrics port: {args.port}")
    logger.info(f"Prometheus URL: {prometheus_url}")
    logger.info(f"Metric to check: {args.metric}")
    logger.info("")
    
    # Run the checks
    metrics_ok, metrics_count = check_metrics_endpoint(args.port)
    if metrics_ok:
        prometheus_ok = check_prometheus_connection(prometheus_url)
        targets_ok = False
        data_ok = False
        
        if prometheus_ok:
            targets_ok = check_prometheus_targets(prometheus_url)
            if targets_ok:
                data_ok = check_metric_data(prometheus_url, args.metric)
        
        # Suggest fixes based on the check results
        suggest_fixes(metrics_ok, prometheus_ok, targets_ok, data_ok)
        
        # Summary
        logger.info("\n=== Summary ===")
        logger.info(f"Metrics endpoint: {'✅ UP' if metrics_ok else '❌ DOWN'} - {metrics_count} metrics")
        logger.info(f"Prometheus: {'✅ UP' if prometheus_ok else '❌ DOWN'}")
        logger.info(f"Target configuration: {'✅ OK' if targets_ok else '❌ Missing'}")
        logger.info(f"Metric data: {'✅ Present' if data_ok else '❌ Missing'}")
        
        # Overall status
        if metrics_ok and prometheus_ok and targets_ok and data_ok:
            logger.info("\n✅ Integration is WORKING CORRECTLY")
            return 0
        else:
            logger.info("\n⚠️ Integration has ISSUES that need to be fixed")
            return 1
    else:
        # If metrics endpoint is down, no point in checking the rest
        suggest_fixes(metrics_ok, False, False, False)
        logger.info("\n❌ Integration check FAILED - metrics endpoint is not accessible")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 