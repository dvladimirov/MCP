# Kubernetes Dashboard System

This comprehensive document explains all components related to the Kubernetes dashboard and dummy data generation system in the MCP project.

## Important Update

**Note: Some functionality described in this document has been deprecated or removed:**

- The direct dashboard update functionality has been removed
- The dashboard population with dummy data has been removed
- Several helper scripts are no longer maintained

**Current Recommended Approach:**
- Use the MCP Runner menu's "Prometheus Tests & Memory Stress" options to:
  - Run the Kubernetes Metrics Generator (for AI Analysis)
  - Run the AI Anomaly Analysis directly

These changes streamline the system by focusing on the core functionality of metrics generation and AI-powered analysis without requiring dashboard integration.

## Overview

The Kubernetes performance dashboard is designed to display and analyze metrics from Kubernetes pods, including:
- CPU usage by pod
- Memory usage by pod
- Disk I/O (reads and writes) by pod
- Network traffic and errors by pod
- Performance anomaly detection and analysis

Since this dashboard would normally require a running Kubernetes cluster, we've implemented a system that generates realistic dummy data to populate the dashboard panels for development, testing, and demonstration purposes.

## Components

### Core Components

1. **Metrics Generator (`scripts/k8s_dummy_data_generator.py`)**: 
   - Generates Prometheus metrics in the same format as those collected from a real Kubernetes cluster
   - Simulates data for CPU usage, memory usage, network traffic, disk I/O, etc.
   - Exposes metrics on an HTTP endpoint to be scraped by Prometheus

2. **AI Anomaly Analysis (`scripts/ai_anomaly_analysis.py`)**:
   - Analyzes detected anomalies using AI techniques
   - Provides remediation recommendations
   - Generates detailed analysis reports

### Utility Scripts

- `kill_k8s_generators.sh` - Terminates running dummy data generator processes
- MCP Runner - Use the MCP runner menu to access Kubernetes dashboard functionality

## Using the System

### Recommended Method

Use the MCP Runner menu to:

1. **Generate Kubernetes Metrics**:
   ```bash
   ./mcp_run
   ```
   Then select:
   - "Prometheus Tests & Memory Stress" from the main menu
   - "Run Kubernetes Metrics Generator (for AI Analysis)" from the sub-menu
   - Follow the prompts to configure and start the metrics generator

2. **Run AI Analysis of Generated Metrics**:
   ```bash
   ./mcp_run
   ```
   Then select:
   - "Prometheus Tests & Memory Stress" from the main menu
   - "Run AI Anomaly Analysis" from the sub-menu
   - Follow the prompts to analyze metrics and generate reports

3. **Alternatively: Direct Command for AI Analysis**:
   ```bash
   ./mcp_run ai-analyze --timeframe=1h
   ```

## Analysis Reports

Analysis reports are generated as Markdown files with detailed information about detected anomalies and AI-powered recommendations for remediation. These files are saved with timestamps in the root directory (e.g., `ai_anomaly_analysis_20250313_001846.md`).

## Troubleshooting

If you encounter issues with the metrics generator:

1. Check if the generator is running:
   ```bash
   ps aux | grep k8s_dummy_data_generator
   ```

2. Kill and restart generators if necessary:
   ```bash
   ./kill_k8s_generators.sh
   ```

3. Verify Prometheus can access metrics:
   ```bash
   curl http://localhost:<port>/metrics
   ```

4. Check Prometheus targets:
   http://localhost:9090/targets 