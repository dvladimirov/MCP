#!/usr/bin/env python3
"""
MCP-Grafana Bridge
A simple bridge service that provides APIs to integrate MCP with Grafana
"""

import os
import json
import logging
from flask import Flask, request, jsonify
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mcp-grafana-bridge')

# Configuration from environment variables
GRAFANA_URL = os.environ.get('GRAFANA_URL', 'http://grafana:3000')
PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://prometheus:9090')
MCP_PORT = int(os.environ.get('MCP_PORT', 8085))
# Use API key if provided, otherwise fall back to basic auth
GRAFANA_API_KEY = os.environ.get('GRAFANA_API_KEY', '')
GRAFANA_USERNAME = os.environ.get('GRAFANA_USERNAME', 'admin')
GRAFANA_PASSWORD = os.environ.get('GRAFANA_PASSWORD', 'admin')

app = Flask(__name__)

def get_grafana_headers():
    """
    Returns the appropriate headers for Grafana API calls.
    Uses API key if available, otherwise falls back to basic auth.
    """
    headers = {"Accept": "application/json"}
    if GRAFANA_API_KEY:
        headers["Authorization"] = f"Bearer {GRAFANA_API_KEY}"
    return headers

def make_grafana_request(method, endpoint, **kwargs):
    """
    Makes a request to the Grafana API with appropriate authentication.
    """
    url = f"{GRAFANA_URL}{endpoint}"
    headers = get_grafana_headers()
    if 'headers' in kwargs:
        kwargs['headers'].update(headers)
    else:
        kwargs['headers'] = headers
    
    if not GRAFANA_API_KEY:
        kwargs['auth'] = (GRAFANA_USERNAME, GRAFANA_PASSWORD)
    
    return requests.request(method, url, **kwargs)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "mcp-grafana-bridge"})

@app.route('/version', methods=['GET'])
def version():
    """Version endpoint"""
    return jsonify({
        "name": "mcp-grafana-bridge",
        "version": "1.0.0",
        "description": "A simple bridge between MCP and Grafana"
    })

@app.route('/grafana/dashboards', methods=['GET'])
def list_dashboards():
    """List all Grafana dashboards"""
    try:
        response = make_grafana_request('GET', '/api/search')
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/grafana/dashboard/<uid>', methods=['GET'])
def get_dashboard(uid):
    """Get a specific Grafana dashboard by UID"""
    try:
        response = make_grafana_request('GET', f'/api/dashboards/uid/{uid}')
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error getting dashboard {uid}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/grafana/datasources', methods=['GET'])
def list_datasources():
    """List all Grafana datasources"""
    try:
        response = make_grafana_request('GET', '/api/datasources')
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error listing datasources: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/prometheus/query', methods=['POST'])
def prometheus_query():
    """Execute a Prometheus query"""
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({"error": "Missing query parameter"}), 400
            
        params = {"query": data['query']}
        if 'time' in data:
            params['time'] = data['time']
            
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params=params
        )
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error executing Prometheus query: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/prometheus/query_range', methods=['POST'])
def prometheus_query_range():
    """Execute a Prometheus range query"""
    try:
        data = request.json
        required_params = ['query', 'start', 'end', 'step']
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"Missing {param} parameter"}), 400
                
        params = {
            "query": data['query'],
            "start": data['start'],
            "end": data['end'],
            "step": data['step']
        }
            
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params=params
        )
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error executing Prometheus range query: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/import/dashboard', methods=['POST'])
def import_dashboard():
    """Import a dashboard to Grafana"""
    try:
        data = request.json
        if not data or 'dashboard' not in data:
            return jsonify({"error": "Missing dashboard definition"}), 400
            
        # Add required fields if not present
        if 'overwrite' not in data:
            data['overwrite'] = True
        if 'message' not in data:
            data['message'] = "Imported by MCP-Grafana Bridge"
            
        response = make_grafana_request(
            'POST', 
            '/api/dashboards/db',
            json=data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error importing dashboard: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    auth_method = "API key" if GRAFANA_API_KEY else "basic auth"
    logger.info(f"Starting MCP-Grafana Bridge on port {MCP_PORT}")
    logger.info(f"Connected to Grafana at {GRAFANA_URL} using {auth_method}")
    logger.info(f"Connected to Prometheus at {PROMETHEUS_URL}")
    app.run(host='0.0.0.0', port=MCP_PORT) 