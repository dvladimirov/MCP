import pytest
import json
import threading
import time
import requests
from unittest.mock import patch, MagicMock
import sys
import os
from http.server import HTTPServer

# Add scripts directory to path to import the metrics generator
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
from k8s_dummy_data_generator import (
    MetricsGenerator, 
    MetricsServer, 
    start_server, 
    DEFAULT_POD_COUNT, 
    HTTP_PORT
)

class TestK8sMetricsGenerator:
    """Tests for the Kubernetes metrics generator"""
    
    @pytest.fixture
    def metrics_generator(self):
        """Create a metrics generator instance for testing"""
        return MetricsGenerator(pod_count=5)  # Use a small number for testing
    
    def test_initialization(self, metrics_generator):
        """Test that metrics generator initializes correctly"""
        # Check that pods were created
        assert len(metrics_generator.pods) == 5
        
        # Check each pod has the required attributes
        for pod in metrics_generator.pods:
            assert "name" in pod
            assert "container_name" in pod
            assert "image" in pod
            assert "node" in pod
            assert "namespace" in pod
            assert "uid" in pod
    
    def test_generate_metrics(self, metrics_generator):
        """Test metrics generation"""
        metrics = metrics_generator.generate_metrics()
        
        # Verify that metrics is a string
        assert isinstance(metrics, str)
        
        # Check that metrics are not empty
        assert len(metrics) > 0
        
        # Check that metrics contain expected labels and values
        metrics_lines = metrics.split("\n")
        assert len(metrics_lines) > 0
        
        # Check for the presence of key metrics
        cpu_metrics = [line for line in metrics_lines if "container_cpu_usage_seconds_total" in line]
        memory_metrics = [line for line in metrics_lines if "container_memory_usage_bytes" in line]
        network_metrics = [line for line in metrics_lines if "container_network" in line]
        
        assert len(cpu_metrics) > 0
        assert len(memory_metrics) > 0
        assert len(network_metrics) > 0
        
        # Check format of a sample metric
        sample_metric = cpu_metrics[0]
        assert "{" in sample_metric and "}" in sample_metric  # Check for labels
        assert "container_name=" in sample_metric  # Check for specific label
        assert "kubernetes_io_hostname=" in sample_metric  # Check for hostname label
        
        # Verify numeric value at the end
        metric_parts = sample_metric.split("}")
        assert len(metric_parts) == 2
        assert metric_parts[1].strip().replace(".", "", 1).isdigit()  # Check if the value is numeric

    @patch("http.server.HTTPServer")
    def test_metrics_server(self, mock_http_server):
        """Test the metrics server initialization"""
        # Create mock objects for the server
        mock_server = MagicMock()
        mock_http_server.return_value = mock_server
        
        # Create a metrics generator
        metrics_generator = MetricsGenerator(pod_count=3)
        
        # Create a mock handler function to use instead of the real one
        def mock_handler_factory(metrics_generator):
            return lambda *args, **kwargs: None
        
        # Create a simple HTTPServer manually to test if it would work
        server = HTTPServer(('0.0.0.0', HTTP_PORT), MetricsServer)
        server.metrics_generator = metrics_generator
        
        # Verify the server can be created without errors
        assert hasattr(server, "metrics_generator")
        
        # Cleanup - we don't actually start this server
        del server

    def test_metrics_server_handler(self):
        """Test the MetricsServer handler"""
        # Create mock objects
        mock_server = MagicMock()
        mock_generator = MagicMock()
        mock_generator.generate_metrics.return_value = "test_metric{label='value'} 1.0"
        mock_server.metrics_generator = mock_generator
        
        # Create mock request handler with minimal required attributes
        mock_wfile = MagicMock()
        
        class MockHandler(MetricsServer):
            def __init__(self):
                self.server = mock_server
                self.path = "/metrics"
                self.wfile = mock_wfile
            
            def send_response(self, code):
                self.response_code = code
            
            def send_header(self, name, value):
                pass
            
            def end_headers(self):
                pass
        
        # Create and test the handler
        handler = MockHandler()
        handler.do_GET()
        
        # Verify that the generator was called
        mock_generator.generate_metrics.assert_called_once()
        
        # Verify that the response code was 200
        assert handler.response_code == 200
        
        # Verify that the metrics were written to the response
        mock_wfile.write.assert_called_once()
        args, kwargs = mock_wfile.write.call_args
        assert b"test_metric" in args[0]
    
    def test_metrics_server_handler_404(self):
        """Test the MetricsServer handler for non-metrics paths"""
        # Create mock objects
        mock_server = MagicMock()
        mock_generator = MagicMock()
        mock_server.metrics_generator = mock_generator
        
        # Create mock request handler with minimal required attributes
        mock_wfile = MagicMock()
        
        class MockHandler(MetricsServer):
            def __init__(self):
                self.server = mock_server
                self.path = "/nonexistent"
                self.wfile = mock_wfile
            
            def send_response(self, code):
                self.response_code = code
            
            def send_header(self, name, value):
                pass
            
            def end_headers(self):
                pass
        
        # Create and test the handler
        handler = MockHandler()
        handler.do_GET()
        
        # Verify that the generator was not called
        mock_generator.generate_metrics.assert_not_called()
        
        # Verify that the response code was 404
        assert handler.response_code == 404
        
        # Verify that "Not Found" was written to the response
        mock_wfile.write.assert_called_once_with(b'Not Found')
    
    @pytest.mark.integration
    def test_metrics_endpoint_integration(self):
        """
        Integration test for the metrics endpoint.
        
        This test starts an actual HTTP server and makes a request to it.
        Run with --run-integration flag to execute this test.
        """
        # Create a metrics generator
        generator = MetricsGenerator(pod_count=2)
        port = 9999  # Use a different port for testing
        
        # Start the server in a background thread
        server_thread = threading.Thread(
            target=start_server,
            args=(port, generator),
            daemon=True
        )
        server_thread.start()
        
        # Give the server time to start
        time.sleep(1)
        
        try:
            # Make a request to the metrics endpoint
            response = requests.get(f"http://localhost:{port}/metrics")
            
            # Verify the response
            assert response.status_code == 200
            assert len(response.text) > 0
            assert "container_cpu_usage_seconds_total" in response.text
            
            # Make a request to a non-existent endpoint
            response_404 = requests.get(f"http://localhost:{port}/nonexistent")
            assert response_404.status_code == 404
            assert response_404.text == "Not Found"
            
        except Exception as e:
            pytest.fail(f"Failed to connect to metrics server: {e}")
        finally:
            # We can't easily stop the server (it's in serve_forever),
            # but it's a daemon thread so it will be terminated when the test exits
            pass 