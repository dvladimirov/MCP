import pytest
import json
from unittest.mock import patch, MagicMock
import requests
from datetime import datetime, timedelta

from mcp.prometheus_service import PrometheusService

class TestPrometheusService:
    """Tests for the PrometheusService class"""
    
    @pytest.fixture
    def prometheus_url(self):
        """Return a test Prometheus URL"""
        return "http://localhost:9090"
    
    @pytest.fixture
    def prom_service(self, prometheus_url):
        """Create a PrometheusService instance for testing"""
        return PrometheusService(prometheus_url)
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock successful response"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": []
            }
        }
        return mock_resp
    
    @patch("requests.get")
    def test_query(self, mock_get, prom_service, mock_response):
        """Test querying Prometheus metrics"""
        # Set up the mock response
        mock_get.return_value = mock_response
        
        # Call the query method
        query_expr = "up"
        result = prom_service.query(query_expr)
        
        # Verify that requests.get was called with the correct URL and parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "http://localhost:9090/api/v1/query"
        assert kwargs["params"]["query"] == query_expr
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
    
    @patch("requests.get")
    def test_query_with_time(self, mock_get, prom_service, mock_response):
        """Test querying Prometheus metrics with a specific time"""
        # Set up the mock response
        mock_get.return_value = mock_response
        
        # Call the query method with a time parameter
        query_expr = "up"
        time_param = "2023-01-01T12:00:00Z"
        result = prom_service.query(query_expr, time_param)
        
        # Verify that requests.get was called with the correct URL and parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "http://localhost:9090/api/v1/query"
        assert kwargs["params"]["query"] == query_expr
        assert kwargs["params"]["time"] == time_param
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
    
    @patch("requests.get")
    def test_query_range(self, mock_get, prom_service, mock_response):
        """Test querying Prometheus metrics over a time range"""
        # Set up the mock response
        mock_get.return_value = mock_response
        
        # Call the query_range method
        query_expr = "rate(container_cpu_usage_seconds_total[5m])"
        start_time = "2023-01-01T00:00:00Z"
        end_time = "2023-01-01T01:00:00Z"
        step = "15s"
        result = prom_service.query_range(query_expr, start_time, end_time, step)
        
        # Verify that requests.get was called with the correct URL and parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "http://localhost:9090/api/v1/query_range"
        assert kwargs["params"]["query"] == query_expr
        assert kwargs["params"]["start"] == start_time
        assert kwargs["params"]["end"] == end_time
        assert kwargs["params"]["step"] == step
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
    
    @patch("requests.get")
    def test_get_series(self, mock_get, prom_service, mock_response):
        """Test getting time series data from Prometheus"""
        # Set up the mock response
        mock_get.return_value = mock_response
        
        # Call the get_series method
        match = ["up", 'container_cpu_usage_seconds_total{container="nginx"}']
        start_time = "2023-01-01T00:00:00Z"
        end_time = "2023-01-01T01:00:00Z"
        result = prom_service.get_series(match, start_time, end_time)
        
        # Verify that requests.get was called with the correct URL and parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "http://localhost:9090/api/v1/series"
        assert kwargs["params"]["match[]"] == match
        assert kwargs["params"]["start"] == start_time
        assert kwargs["params"]["end"] == end_time
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
    
    @patch("requests.get")
    def test_get_labels(self, mock_get, prom_service, mock_response):
        """Test getting all label names from Prometheus"""
        # Set up the mock response with label data
        mock_response.json.return_value = {
            "status": "success",
            "data": ["job", "instance", "container", "name"]
        }
        mock_get.return_value = mock_response
        
        # Call the get_labels method
        result = prom_service.get_labels()
        
        # Verify that requests.get was called with the correct URL
        mock_get.assert_called_once_with("http://localhost:9090/api/v1/labels")
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
        assert "job" in result["data"]
        assert "container" in result["data"]
    
    @patch("requests.get")
    def test_get_label_values(self, mock_get, prom_service, mock_response):
        """Test getting values for a specific label from Prometheus"""
        # Set up the mock response with label values
        mock_response.json.return_value = {
            "status": "success",
            "data": ["prometheus", "node-exporter", "cadvisor"]
        }
        mock_get.return_value = mock_response
        
        # Call the get_label_values method
        label_name = "job"
        result = prom_service.get_label_values(label_name)
        
        # Verify that requests.get was called with the correct URL
        mock_get.assert_called_once_with(f"http://localhost:9090/api/v1/label/{label_name}/values")
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
        assert "prometheus" in result["data"]
        assert "node-exporter" in result["data"]
    
    @patch("requests.get")
    def test_get_targets(self, mock_get, prom_service):
        """Test getting all targets from Prometheus"""
        # Set up a mock response with targets data
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "success",
            "data": {
                "activeTargets": [
                    {
                        "discoveredLabels": {"job": "prometheus", "instance": "localhost:9090"},
                        "labels": {"job": "prometheus", "instance": "localhost:9090"},
                        "scrapePool": "prometheus",
                        "scrapeUrl": "http://localhost:9090/metrics",
                        "lastError": "",
                        "lastScrape": "2023-01-01T00:00:00.000Z",
                        "health": "up"
                    }
                ]
            }
        }
        mock_get.return_value = mock_resp
        
        # Call the get_targets method
        result = prom_service.get_targets()
        
        # Verify that requests.get was called with the correct URL
        mock_get.assert_called_once_with("http://localhost:9090/api/v1/targets")
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
        assert "activeTargets" in result["data"]
        assert len(result["data"]["activeTargets"]) == 1
        assert result["data"]["activeTargets"][0]["health"] == "up"
    
    @patch("requests.get")
    def test_get_rules(self, mock_get, prom_service):
        """Test getting all alerting rules from Prometheus"""
        # Set up a mock response with rules data
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "success",
            "data": {
                "groups": [
                    {
                        "name": "example",
                        "file": "example.yml",
                        "rules": [
                            {
                                "name": "HighCPULoad",
                                "query": "node_load1 > 2",
                                "duration": 300,
                                "labels": {"severity": "warning"},
                                "annotations": {"summary": "High CPU load detected"}
                            }
                        ]
                    }
                ]
            }
        }
        mock_get.return_value = mock_resp
        
        # Call the get_rules method
        result = prom_service.get_rules()
        
        # Verify that requests.get was called with the correct URL
        mock_get.assert_called_once_with("http://localhost:9090/api/v1/rules")
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
        assert "groups" in result["data"]
        assert len(result["data"]["groups"]) == 1
        assert result["data"]["groups"][0]["name"] == "example"
        assert len(result["data"]["groups"][0]["rules"]) == 1
    
    @patch("requests.get")
    def test_get_alerts(self, mock_get, prom_service):
        """Test getting all alerts from Prometheus"""
        # Set up a mock response with alerts data
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "success",
            "data": {
                "alerts": [
                    {
                        "labels": {
                            "alertname": "HighCPULoad",
                            "instance": "localhost:9100",
                            "severity": "warning"
                        },
                        "annotations": {
                            "summary": "High CPU load detected"
                        },
                        "state": "firing",
                        "activeAt": "2023-01-01T00:00:00.000Z",
                        "value": "3.14"
                    }
                ]
            }
        }
        mock_get.return_value = mock_resp
        
        # Call the get_alerts method
        result = prom_service.get_alerts()
        
        # Verify that requests.get was called with the correct URL
        mock_get.assert_called_once_with("http://localhost:9090/api/v1/alerts")
        
        # Verify the result
        assert result["status"] == "success"
        assert "data" in result
        assert "alerts" in result["data"]
        assert len(result["data"]["alerts"]) == 1
        assert result["data"]["alerts"][0]["labels"]["alertname"] == "HighCPULoad"
        assert result["data"]["alerts"][0]["state"] == "firing"
    
    @patch("requests.get")
    def test_handle_request_error(self, mock_get, prom_service):
        """Test handling errors from Prometheus API requests"""
        # Set up the mock to raise an exception
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        # Call the query method and expect it to handle the error
        query_expr = "up"
        result = prom_service.query(query_expr)
        
        # Verify the result contains the error information
        assert result["status"] == "error"
        assert "error" in result
        assert "Connection error" in result["error"] 