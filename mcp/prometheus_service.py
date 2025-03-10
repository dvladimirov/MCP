import requests
import json
from typing import Dict, Any, List, Optional

class PrometheusService:
    """Service for interacting with Prometheus metrics APIs"""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        """Initialize the Prometheus service
        
        Args:
            prometheus_url: The URL of the Prometheus server (default: http://localhost:9090)
        """
        self.prometheus_url = prometheus_url.rstrip('/')
    
    def query(self, query_expr: str, time: Optional[str] = None) -> Dict[str, Any]:
        """Execute an instant query against Prometheus
        
        Args:
            query_expr: PromQL query expression
            time: Evaluation timestamp (rfc3339 or unix_timestamp), optional
            
        Returns:
            Dict[str, Any]: Query result
        """
        endpoint = f"{self.prometheus_url}/api/v1/query"
        params = {'query': query_expr}
        
        if time:
            params['time'] = time
            
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }
    
    def query_range(self, query_expr: str, start: str, end: str, step: str) -> Dict[str, Any]:
        """Execute a range query against Prometheus
        
        Args:
            query_expr: PromQL query expression
            start: Start timestamp (rfc3339 or unix_timestamp)
            end: End timestamp (rfc3339 or unix_timestamp)
            step: Query resolution step width (duration format or float seconds)
            
        Returns:
            Dict[str, Any]: Range query result
        """
        endpoint = f"{self.prometheus_url}/api/v1/query_range"
        params = {
            'query': query_expr,
            'start': start,
            'end': end,
            'step': step
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }
    
    def get_series(self, match: List[str], start: Optional[str] = None, end: Optional[str] = None) -> Dict[str, Any]:
        """Find series matching a label set
        
        Args:
            match: Series selector string array that selects the series to return
            start: Start timestamp (rfc3339 or unix_timestamp), optional
            end: End timestamp (rfc3339 or unix_timestamp), optional
            
        Returns:
            Dict[str, Any]: Series data
        """
        endpoint = f"{self.prometheus_url}/api/v1/series"
        params = {'match[]': match}
        
        if start:
            params['start'] = start
        if end:
            params['end'] = end
            
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }
    
    def get_labels(self) -> Dict[str, Any]:
        """Get all label names
        
        Returns:
            Dict[str, Any]: Label names
        """
        endpoint = f"{self.prometheus_url}/api/v1/labels"
        
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }
    
    def get_label_values(self, label_name: str) -> Dict[str, Any]:
        """Get values for a label
        
        Args:
            label_name: Label name
            
        Returns:
            Dict[str, Any]: Label values
        """
        endpoint = f"{self.prometheus_url}/api/v1/label/{label_name}/values"
        
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }
    
    def get_targets(self) -> Dict[str, Any]:
        """Get targets
        
        Returns:
            Dict[str, Any]: Targets information
        """
        endpoint = f"{self.prometheus_url}/api/v1/targets"
        
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }
    
    def get_rules(self) -> Dict[str, Any]:
        """Get rules
        
        Returns:
            Dict[str, Any]: Rules information
        """
        endpoint = f"{self.prometheus_url}/api/v1/rules"
        
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }
    
    def get_alerts(self) -> Dict[str, Any]:
        """Get alerts
        
        Returns:
            Dict[str, Any]: Alerts information
        """
        endpoint = f"{self.prometheus_url}/api/v1/alerts"
        
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "data": None
            } 