#!/usr/bin/env python3
"""
AI Anomaly Analysis
Analyzes Kubernetes anomalies and provides AI-powered remediation suggestions
"""

import os
import json
import time
import sys
import logging
import argparse
import requests
import re
from datetime import datetime, timedelta
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai-anomaly-analysis')

# Configuration
MCP_SERVER_URL = os.environ.get('MCP_SERVER_URL', 'http://localhost:8000')
DEFAULT_TIMEFRAME = '1h'  # Last hour by default
SIMULATOR_OUTPUT_FILE = os.environ.get('SIMULATOR_OUTPUT_FILE', 'simulator_output.txt')
SIMULATOR_DATA_FILE = os.environ.get('K8S_SIMULATOR_DATA', 'k8s_simulator_data.json')

class AIAnomalyAnalyzer:
    """Analyzes Kubernetes anomalies using AI and provides remediation suggestions"""
    
    def __init__(self, timeframe=DEFAULT_TIMEFRAME, verbose=False, model=None, simulator_data=None):
        self.timeframe = timeframe
        self.verbose = verbose
        self.preferred_model = model
        self.anomalies = None
        self.simulator_anomalies = []
        self.simulator_data_file = simulator_data if simulator_data else SIMULATOR_DATA_FILE
        self.promql_queries = {}
        
        logger.info(f"AI Anomaly Analyzer initialized with timeframe: {timeframe}")
        if model:
            logger.info(f"Using specified model: {model}")
        
        # Load Grafana queries if available
        self._load_promql_queries()
    
    def _load_promql_queries(self):
        """Load Grafana/Prometheus queries from the queries library"""
        try:
            queries_file = os.path.join('grafana', 'queries', 'kubernetes_queries.json')
            if os.path.exists(queries_file):
                with open(queries_file, 'r') as f:
                    import json
                    data = json.load(f)
                    
                    # Extract queries by category
                    for category, info in data.get('categories', {}).items():
                        for query_name, query_data in info.get('queries', {}).items():
                            self.promql_queries[f"{category}_{query_name}"] = query_data
                    
                    logger.info(f"Loaded {len(self.promql_queries)} Prometheus queries from library")
            else:
                logger.warning(f"Could not find queries file at {queries_file}")
        except Exception as e:
            logger.error(f"Error loading Prometheus queries: {e}")
    
    def _detect_anomalies_from_prometheus(self):
        """Detect anomalies by querying Prometheus directly"""
        try:
            import requests
            prometheus_url = "http://localhost:9090"
            
            logger.info("No anomalies found in simulator data, querying Prometheus directly")
            
            # Check if Prometheus is accessible
            try:
                response = requests.get(f"{prometheus_url}/api/v1/status/config", timeout=5)
                if response.status_code != 200:
                    logger.warning(f"Prometheus is not accessible at {prometheus_url}")
                    return False
                logger.info("Successfully connected to Prometheus")
            except Exception as e:
                logger.warning(f"Error connecting to Prometheus: {e}")
                return False
            
            # Use the promql queries loaded from library to detect anomalies
            detected_anomalies = []
            
            # CPU usage spikes
            if "anomaly_detection_cpu_spikes" in self.promql_queries:
                query = self.promql_queries["anomaly_detection_cpu_spikes"]["query"]
            else:
                query = "rate(container_cpu_usage_seconds_total{container_name!='POD',container_name!='',pod!=''}[5m]) > 0.8"
            
            try:
                response = requests.get(
                    f"{prometheus_url}/api/v1/query",
                    params={"query": query},
                    timeout=10
                )
                if response.status_code == 200 and response.json()["status"] == "success":
                    result = response.json()["data"]["result"]
                    for item in result:
                        pod = item["metric"].get("pod", "unknown-pod")
                        if pod == "unknown-pod" and "container" in item["metric"]:
                            pod = item["metric"]["container"]
                        node = item["metric"].get("kubernetes_io_hostname", "unknown-node")
                        namespace = item["metric"].get("namespace", "default")
                        value = float(item["value"][1]) if len(item["value"]) > 1 else 0
                        
                        detected_anomalies.append({
                            'type': 'cpu',
                            'pod': pod,
                            'node': node,
                            'namespace': namespace,
                            'value': value * 100,  # Convert to percentage
                            'timestamp': datetime.now().isoformat(),
                            'description': f"CPU usage spike of {value*100:.1f}% detected",
                            'severity': 'high' if value > 0.9 else 'medium'
                        })
                    
                    if detected_anomalies:
                        logger.info(f"Found {len(detected_anomalies)} CPU anomalies in Prometheus")
            except Exception as e:
                logger.warning(f"Error querying CPU anomalies: {e}")
            
            # Memory usage spikes
            if "anomaly_detection_memory_spikes" in self.promql_queries:
                query = self.promql_queries["anomaly_detection_memory_spikes"]["query"]
            else:
                query = "container_memory_usage_bytes{container_name!='POD',container_name!='',pod!=''} > 1073741824"
            
            try:
                response = requests.get(
                    f"{prometheus_url}/api/v1/query",
                    params={"query": query},
                    timeout=10
                )
                if response.status_code == 200 and response.json()["status"] == "success":
                    result = response.json()["data"]["result"]
                    for item in result:
                        pod = item["metric"].get("pod", "unknown-pod")
                        if pod == "unknown-pod" and "container" in item["metric"]:
                            pod = item["metric"]["container"]
                        node = item["metric"].get("kubernetes_io_hostname", "unknown-node")
                        namespace = item["metric"].get("namespace", "default")
                        value = float(item["value"][1]) if len(item["value"]) > 1 else 0
                        value_mb = value / (1024 * 1024)  # Convert to MB
                        
                        detected_anomalies.append({
                            'type': 'memory',
                            'pod': pod,
                            'node': node,
                            'namespace': namespace,
                            'value': value_mb,
                            'timestamp': datetime.now().isoformat(),
                            'description': f"Memory usage spike of {value_mb:.1f}MB detected",
                            'severity': 'high' if value_mb > 2048 else 'medium'
                        })
                    
                    if detected_anomalies:
                        logger.info(f"Found {len(detected_anomalies) - len([a for a in detected_anomalies if a['type'] == 'cpu'])} memory anomalies in Prometheus")
            except Exception as e:
                logger.warning(f"Error querying memory anomalies: {e}")
            
            # If we found anomalies, return them
            if detected_anomalies:
                self.simulator_anomalies = detected_anomalies
                return True
            else:
                logger.warning("No anomalies detected in Prometheus data")
                return False
                
        except Exception as e:
            logger.error(f"Error detecting anomalies from Prometheus: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def fetch_anomalies(self):
        """Fetch the latest anomalies from structured data file"""
        try:
            # First check for the structured JSON data file
            self._parse_structured_data()
            
            # If that doesn't yield results, fall back to simulator logs
            if not self.simulator_anomalies:
                self._parse_simulator_logs()
            
            # If we still don't have anomalies, try querying Prometheus directly
            if not self.simulator_anomalies:
                logger.info("No anomalies found in simulator files, trying Prometheus")
                self._detect_anomalies_from_prometheus()
            
            # Create a synthetic anomaly structure from simulator data
            if self.simulator_anomalies:
                self.anomalies = {
                    'detected_anomalies': [
                        {
                            'id': str(uuid.uuid4()),
                            'timestamp': anomaly.get('timestamp', datetime.now().isoformat()),
                            'resource_type': 'kubernetes_pod',
                            'resource_name': anomaly.get('pod', 'unknown-pod'),
                            'node': anomaly.get('node', 'unknown-node'),
                            'namespace': anomaly.get('namespace', 'default'),
                            'metric_name': f"{anomaly.get('type', 'unknown')}_usage",
                            'value': anomaly.get('value', 0),
                            'threshold': 0.8 if anomaly.get('type') == 'cpu' else 800,
                            'severity': anomaly.get('severity', 'medium'),
                            'anomaly_type': 'spike' if anomaly.get('type') in ['cpu', 'memory'] else 'unusual_activity',
                            'description': anomaly.get('description', f"Unusual {anomaly.get('type', 'resource')} usage detected"),
                            'is_active': True
                        }
                        for anomaly in self.simulator_anomalies
                    ],
                    'total': len(self.simulator_anomalies),
                    'timeframe': self.timeframe
                }
                return self.anomalies
            else:
                # Even if we don't have anomalies, we should return some context for the AI to analyze
                logger.warning("No anomalies found in any data source")
                return {
                    'detected_anomalies': [],
                    'total': 0,
                    'timeframe': self.timeframe,
                    'context': "No anomalies were detected in any data source. The system appears to be operating normally."
                }
        except Exception as e:
            logger.error(f"Error fetching anomalies: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {'detected_anomalies': [], 'total': 0, 'timeframe': self.timeframe}
    
    def _parse_structured_data(self):
        """Parse the structured JSON data file exported by the simulator"""
        try:
            if os.path.exists(self.simulator_data_file):
                logger.info(f"Using structured data from {self.simulator_data_file}")
                with open(self.simulator_data_file, 'r') as f:
                    import json
                    data = json.load(f)
                
                # Extract anomalies from the structured data
                anomalies = data.get('anomalies', [])
                if anomalies:
                    logger.info(f"Found {len(anomalies)} anomalies in structured data")
                    self.simulator_anomalies = anomalies
                    
                    # Also store the Prometheus queries for later use
                    if 'prometheus_queries' in data:
                        for key, query in data['prometheus_queries'].items():
                            self.promql_queries[f"simulator_{key}"] = {
                                'query': query,
                                'description': f"Simulator recommended query for {key}",
                                'unit': 'varies'
                            }
                        logger.info(f"Added {len(data['prometheus_queries'])} simulator queries")
                else:
                    logger.info("No anomalies found in structured data")
            else:
                logger.info(f"Structured data file {self.simulator_data_file} not found")
        except Exception as e:
            logger.error(f"Error parsing structured data: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
    
    def _parse_simulator_logs(self):
        """Look for simulator-generated anomalies in the logs (fallback method)"""
        try:
            # Read latest docker logs for k8s-pod-simulator
            log_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - k8s-pod-simulator - INFO - Generated (.*?) anomaly in pod (.*?):"
            
            # Patterns for different anomaly types
            cpu_pattern = r"Generated CPU anomaly in pod (.*?): (\d+\.\d+)%"
            memory_pattern = r"Generated memory anomaly in pod (.*?): growth \+(\d+\.\d+)MB"
            disk_pattern = r"Generated disk I/O anomaly in pod (.*?): (\d+\.\d+)x increase"
            network_traffic_pattern = r"Generated network traffic anomaly in pod (.*?): (\d+\.\d+)x increase"
            network_error_pattern = r"Generated network error anomaly in pod (.*?)"
            
            # Try to find simulator logs from the current directory
            logs = []
            
            # First try to read docker container logs if possible
            try:
                import subprocess
                result = subprocess.run(['docker', 'logs', '--tail', '100', 'k8s-pod-simulator'], 
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    logs = result.stdout.split('\n')
            except Exception as e:
                logger.warning(f"Could not get logs from docker: {e}")
            
            # If that fails, look for log files in the current directory
            if not logs:
                for filename in os.listdir('.'):
                    if 'k8s-pod-simulator' in filename and filename.endswith('.log'):
                        with open(filename, 'r') as f:
                            logs = f.readlines()
                        break
            
            # If still no logs, try to check the script output directly
            if not logs:
                # Check if we're running right after the simulator
                simulator_output_file = SIMULATOR_OUTPUT_FILE
                if os.path.exists(simulator_output_file):
                    logger.info(f"Using simulator output from {simulator_output_file}")
                    with open(simulator_output_file, 'r') as f:
                        logs = f.readlines()
                else:
                    logger.warning(f"Could not find simulator output file: {simulator_output_file}")
            
            # Process logs
            self.simulator_anomalies = []
            
            for line in logs:
                # Try to extract CPU anomalies
                cpu_match = re.search(cpu_pattern, line)
                if cpu_match:
                    pod_name = cpu_match.group(1)
                    cpu_value = float(cpu_match.group(2))
                    
                    # Extract node from pod name based on pod template patterns
                    node = self._extract_node_from_pod(pod_name)
                    
                    timestamp = datetime.now().isoformat()
                    timestamp_match = re.search(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})", line)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)
                        
                    self.simulator_anomalies.append({
                        'type': 'cpu',
                        'pod': pod_name,
                        'node': node,
                        'value': cpu_value,
                        'timestamp': timestamp,
                        'description': f"CPU usage spike of {cpu_value}% detected",
                        'severity': 'high' if cpu_value > 90 else 'medium'
                    })
                    continue
                
                # Try to extract memory anomalies
                memory_match = re.search(memory_pattern, line)
                if memory_match:
                    pod_name = memory_match.group(1)
                    growth_mb = float(memory_match.group(2))
                    
                    # Extract node from pod name
                    node = self._extract_node_from_pod(pod_name)
                    
                    timestamp = datetime.now().isoformat()
                    timestamp_match = re.search(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})", line)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)
                        
                    self.simulator_anomalies.append({
                        'type': 'memory',
                        'pod': pod_name,
                        'node': node,
                        'value': growth_mb,
                        'timestamp': timestamp,
                        'description': f"Memory growth of {growth_mb}MB detected",
                        'severity': 'high' if growth_mb > 1000 else 'medium'
                    })
                    continue
                
                # Try to extract disk I/O anomalies
                disk_match = re.search(disk_pattern, line)
                if disk_match:
                    pod_name = disk_match.group(1)
                    disk_multiplier = float(disk_match.group(2))
                    
                    # Extract node from pod name
                    node = self._extract_node_from_pod(pod_name)
                    
                    timestamp = datetime.now().isoformat()
                    timestamp_match = re.search(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})", line)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)
                        
                    self.simulator_anomalies.append({
                        'type': 'disk',
                        'pod': pod_name,
                        'node': node,
                        'value': disk_multiplier,
                        'timestamp': timestamp,
                        'description': f"Disk I/O increase of {disk_multiplier}x detected",
                        'severity': 'high' if disk_multiplier > 5 else 'medium'
                    })
                    continue
                
                # Try to extract network traffic anomalies
                network_match = re.search(network_traffic_pattern, line)
                if network_match:
                    pod_name = network_match.group(1)
                    network_multiplier = float(network_match.group(2))
                    
                    # Extract node from pod name
                    node = self._extract_node_from_pod(pod_name)
                    
                    timestamp = datetime.now().isoformat()
                    timestamp_match = re.search(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})", line)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)
                        
                    self.simulator_anomalies.append({
                        'type': 'network',
                        'pod': pod_name,
                        'node': node,
                        'value': network_multiplier,
                        'timestamp': timestamp,
                        'description': f"Network traffic increase of {network_multiplier}x detected",
                        'severity': 'high' if network_multiplier > 10 else 'medium'
                    })
                    continue
                
                # Try to extract network error anomalies
                error_match = re.search(network_error_pattern, line)
                if error_match:
                    pod_name = error_match.group(1)
                    
                    # Extract node from pod name
                    node = self._extract_node_from_pod(pod_name)
                    
                    timestamp = datetime.now().isoformat()
                    timestamp_match = re.search(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})", line)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)
                        
                    self.simulator_anomalies.append({
                        'type': 'network_error',
                        'pod': pod_name,
                        'node': node,
                        'value': 1.0,  # Just a placeholder
                        'timestamp': timestamp,
                        'description': "Network error rate increase detected",
                        'severity': 'high'
                    })
                    continue
                
            logger.info(f"Found {len(self.simulator_anomalies)} anomalies in simulator logs")
        except Exception as e:
            logger.error(f"Error parsing simulator logs: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
    
    def _extract_node_from_pod(self, pod_name):
        """Extract the likely node from pod name based on pod prefix"""
        # This is just a heuristic to assign pods to different nodes for the analysis
        if 'nginx' in pod_name:
            return 'worker-1'
        elif 'postgres' in pod_name:
            return 'worker-2'
        elif 'redis' in pod_name:
            return 'worker-1'
        elif 'batch-job' in pod_name:
            return 'worker-2'
        elif 'prometheus' in pod_name:
            return 'master-1'
        else:
            return 'worker-1'
    
    def trigger_anomaly_scan(self):
        """Trigger a new anomaly detection scan"""
        try:
            logger.info("Triggering anomaly scan...")
            
            # Try to get anomalies from structured data or simulator logs
            anomalies_result = self.fetch_anomalies()
            
            if anomalies_result:
                if 'detected_anomalies' in anomalies_result and anomalies_result['detected_anomalies']:
                    logger.info(f"Successfully detected {len(anomalies_result['detected_anomalies'])} anomalies")
                    return True
                elif 'context' in anomalies_result:
                    logger.info("No anomalies found, but system data was successfully processed")
                    return True
                else:
                    logger.warning("Scan completed but no anomalies were found")
                    return True  # Return true even if no anomalies, as long as the scan worked
            else:
                logger.warning("Anomaly scan did not return any results")
                return True  # Still return true to allow for "no anomalies" analysis
        
        except Exception as e:
            logger.error(f"Error during anomaly scan: {e}")
            return False
    
    def check_available_models(self):
        """Check which AI models are available on the MCP server"""
        try:
            # Try to get the list of available models
            logger.info(f"Checking available models at {MCP_SERVER_URL}...")
            response = requests.get(f"{MCP_SERVER_URL}/v1/models", timeout=5)
            
            available_models = []
            if response.status_code == 200:
                models_data = response.json()
                if 'models' in models_data:
                    for model in models_data['models']:
                        model_id = model.get('id')
                        if model_id and 'ModelCapability.CHAT' in str(model.get('capabilities', [])):
                            available_models.append(model_id)
                    
                    logger.info(f"Found available chat models: {', '.join(available_models)}")
                    return available_models
            
            logger.warning(f"Failed to get model list: Status code {response.status_code}")
            return ["openai-gpt-chat", "azure-gpt-4"]  # Default fallback models to try
        except Exception as e:
            logger.warning(f"Error checking available models: {e}")
            return ["openai-gpt-chat", "azure-gpt-4"]  # Default fallback models to try
    
    def analyze_with_ai(self):
        """Send anomalies to the AI for analysis and remediation suggestions"""
        if not self.anomalies:
            logger.warning("No anomalies available for analysis")
            # Create a minimal context for the AI to explain the lack of anomalies
            context = {
                "status": "no_anomalies",
                "timeframe": self.timeframe,
                "timestamp": datetime.now().isoformat(),
                "system_info": self._get_system_info(),
                "message": "No anomalies were detected during the analysis period."
            }
        else:
            # Prepare context for the AI
            context = {
                "anomalies": self.anomalies,
                "timeframe": self.timeframe,
                "timestamp": datetime.now().isoformat(),
                "system_info": self._get_system_info(),
                "simulator_anomalies": self.simulator_anomalies
            }
        
        try:
            # Call MCP server for AI analysis
            logger.info("Sending data to AI for analysis...")
            
            # If a preferred model is specified, use it first
            if self.preferred_model:
                model_endpoints = [self.preferred_model]
                logger.info(f"Using specified model: {self.preferred_model}")
            else:
                # Get available models from the server
                model_endpoints = self.check_available_models()
                
                # If no models were found, use default ones
                if not model_endpoints:
                    model_endpoints = ["openai-gpt-chat", "azure-gpt-4"]
            
            # Try each model endpoint until one works
            ai_response = None
            for model in model_endpoints:
                try:
                    logger.info(f"Attempting to use model endpoint: {model}")
                    
                    # Prepare the prompt based on whether we have anomalies or not
                    if "status" in context and context["status"] == "no_anomalies":
                        system_message = "You are an expert Kubernetes administrator. The system has been analyzed and no anomalies were detected. Explain what this means and provide recommendations for monitoring."
                        user_message = f"No anomalies were detected in the Kubernetes system during the past {self.timeframe} timeframe. Please explain what this means and provide recommendations for continued monitoring and best practices. Include some example Prometheus queries that could be useful for future monitoring: {json.dumps(context, indent=2)}"
                    else:
                        system_message = "You are an expert Kubernetes administrator. Analyze the provided anomalies and suggest remediation actions."
                        user_message = f"Analyze these Kubernetes anomalies and suggest specific remediation actions. Be specific with commands that could be used: {json.dumps(context, indent=2)}"
                    
                    response = requests.post(
                        f"{MCP_SERVER_URL}/v1/models/{model}/chat",
                        json={
                            "messages": [
                                {
                                    "role": "system",
                                    "content": system_message
                                },
                                {
                                    "role": "user",
                                    "content": user_message
                                }
                            ],
                            "max_tokens": 1000,
                            "temperature": 0.5
                        },
                        timeout=30  # Add a longer timeout to give the model time to respond
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully received response from {model} endpoint")
                        ai_response = response.json()
                        analysis = ai_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                        return analysis
                    else:
                        error_msg = f"Model {model} returned status code {response.status_code}"
                        try:
                            error_details = response.json()
                            error_msg += f": {json.dumps(error_details)}"
                        except:
                            pass
                        logger.warning(error_msg)
                        
                except Exception as e:
                    logger.warning(f"Error calling {model} endpoint: {e}")
            
            # If we get here, all model endpoints failed
            logger.error("All AI service endpoints failed. Unable to perform analysis.")
            return "# Analysis Report\n\n" + \
                   ("## No Anomalies Detected\n\nNo anomalies were detected in the Kubernetes system during the past " + 
                    f"{self.timeframe} timeframe. This suggests the system is operating normally.\n\n" if "status" in context and context["status"] == "no_anomalies" else "") + \
                   "Unable to connect to AI services for detailed analysis. Please check:\n\n" + \
                   "1. MCP server is running and accessible\n" + \
                   "2. AI model endpoints are configured correctly\n" + \
                   "3. Network connectivity to AI services\n"
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return "# Analysis Error\n\nAn error occurred during analysis: " + str(e)
    
    def _get_system_info(self):
        """Get basic system information for context"""
        try:
            # Try to get information about the cluster
            # In a real environment, this would query the Kubernetes API
            return {
                "os": os.uname().sysname,
                "hostname": os.uname().nodename,
                "timestamp": datetime.now().isoformat()
            }
        except Exception:
            return {}
    
    def run_analysis(self):
        """Run the complete analysis workflow"""
        # First trigger a fresh scan
        if not self.trigger_anomaly_scan():
            logger.warning("Failed to detect anomalies from any data sources")
            logger.info("Will proceed with analysis of the current system state")
        
        # Perform AI analysis - this will now handle both anomaly and no-anomaly cases
        analysis = self.analyze_with_ai()
        
        if not analysis:
            logger.error("AI analysis failed completely")
            print("\nAnalysis could not be completed. See logs for details.")
            return False
        
        # Print the analysis
        print("\n" + "="*80)
        print("AI ANOMALY ANALYSIS REPORT")
        print("="*80 + "\n")
        print(analysis)
        print("\n" + "="*80)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_anomaly_analysis_{timestamp}.md"
        
        try:
            with open(filename, 'w') as f:
                f.write(analysis)
            
            logger.info(f"Analysis saved to {filename}")
            print(f"\nReport saved to: {filename}")
        except Exception as e:
            logger.error(f"Error saving analysis to file: {e}")
        
        return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='AI-powered Kubernetes anomaly analysis')
    parser.add_argument('--timeframe', type=str, default=DEFAULT_TIMEFRAME, 
                        help='Timeframe to analyze (e.g., 15m, 1h, 6h, 1d)')
    parser.add_argument('--verbose', action='store_true', 
                        help='Enable verbose output')
    parser.add_argument('--model', type=str, 
                        help='Specify which AI model to use (e.g., openai-gpt-chat, azure-gpt-4)')
    parser.add_argument('--list-models', action='store_true',
                        help='List available AI models and exit')
    # Add support for simulator-data
    parser.add_argument('--simulator-data', type=str, 
                        help='Path to the K8s simulator data JSON file')
    # Legacy support for simulator-output
    parser.add_argument('--simulator-output', type=str,
                        help='Path to the simulator output file (deprecated, use --simulator-data instead)')
    
    return parser.parse_args()

def list_available_models():
    """List available AI models from the MCP server"""
    try:
        print(f"Checking available models at {MCP_SERVER_URL}...")
        response = requests.get(f"{MCP_SERVER_URL}/v1/models", timeout=5)
        
        if response.status_code == 200:
            models_data = response.json()
            if 'models' in models_data and models_data['models']:
                print("\nAvailable models:")
                print("-----------------")
                
                for model in models_data['models']:
                    model_id = model.get('id', 'unknown')
                    model_name = model.get('name', 'Unknown')
                    capabilities = model.get('capabilities', [])
                    
                    # Convert capabilities to readable format
                    cap_str = ', '.join([cap.replace('ModelCapability.', '') for cap in capabilities])
                    
                    print(f"ID: {model_id}")
                    print(f"Name: {model_name}")
                    print(f"Capabilities: {cap_str}")
                    print("-----------------")
                
                return True
            else:
                print("No models found on the MCP server.")
                return False
        else:
            print(f"Failed to get model list: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Error checking available models: {e}")
        return False

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Check if we just need to list models
    if args.list_models:
        print("\n" + "="*80)
        print(" AVAILABLE AI MODELS")
        print("="*80 + "\n")
        
        if list_available_models():
            sys.exit(0)
        else:
            sys.exit(1)
    
    print("\n" + "="*80)
    print(" AI-POWERED KUBERNETES ANOMALY ANALYSIS")
    print("="*80 + "\n")
    
    # Handle simulator data path
    simulator_data_path = None
    if args.simulator_data:
        simulator_data_path = args.simulator_data
        print(f"Using simulator data from: {simulator_data_path}")
    elif args.simulator_output:
        # Legacy support
        os.environ['SIMULATOR_OUTPUT_FILE'] = args.simulator_output
        print(f"Using legacy simulator output from: {args.simulator_output}")
        print("Note: --simulator-output is deprecated, please use --simulator-data instead")
    
    # First check if MCP server is available
    try:
        print(f"Checking MCP server connection at {MCP_SERVER_URL}...")
        response = requests.get(f"{MCP_SERVER_URL}/v1/models", timeout=5)
        if response.status_code == 200:
            print(f"✅ MCP server is available")
            # Display available models
            models_data = response.json()
            if 'models' in models_data:
                chat_models = []
                for model in models_data['models']:
                    model_id = model.get('id')
                    if model_id and 'ModelCapability.CHAT' in str(model.get('capabilities', [])):
                        chat_models.append(model_id)
                
                if chat_models:
                    print(f"✅ Available chat models: {', '.join(chat_models)}")
                    
                    # Warn if specified model is not available
                    if args.model and args.model not in chat_models:
                        print(f"⚠️  Specified model '{args.model}' not found in available models")
                else:
                    print("⚠️  No chat models found in MCP server")
        else:
            print(f"⚠️  MCP server returned status code {response.status_code}")
    except Exception as e:
        print(f"⚠️  Unable to connect to MCP server: {e}")
        print("   Will fall back to simulated analysis if needed")
    
    print("\nAnalyzing Kubernetes anomalies and generating remediation suggestions...")
    print(f"Timeframe: {args.timeframe}")
    if args.model:
        print(f"Using specified model: {args.model}")
    
    # Create and run the analyzer
    analyzer = AIAnomalyAnalyzer(
        timeframe=args.timeframe,
        verbose=args.verbose,
        model=args.model,
        simulator_data=simulator_data_path
    )
    
    success = analyzer.run_analysis()
    
    if not success:
        print("\nAnalysis completed with errors. See logs for details.")
        sys.exit(1)
    
    print("\nAnalysis completed successfully!")
    sys.exit(0)

if __name__ == "__main__":
    main() 
