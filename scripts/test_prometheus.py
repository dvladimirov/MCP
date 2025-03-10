#!/usr/bin/env python3
"""
Test the Prometheus integration with MCP with a focus on memory metrics and alerts
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from langflow import MCPAIComponent

def test_prometheus(prometheus_url=None):
    """Test the Prometheus integration with MCP"""
    
    # Use provided Prometheus URL or default
    if prometheus_url is None:
        prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    
    print(f"Testing Prometheus integration with URL: {prometheus_url}")
    
    # Create MCPAIComponent with environment URL or default
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    print(f"Connecting to MCP server at: {mcp_server_url}")
    
    # Initialize the client
    mcp = MCPAIComponent(mcp_server_url=mcp_server_url)
    
    # Set the PROMETHEUS_URL environment variable for the server
    os.environ["PROMETHEUS_URL"] = prometheus_url
    
    # Basic query test
    print("\n1. Testing basic Prometheus query...")
    try:
        query_result = mcp.prometheus_query("up")
        print(f"Query status: {query_result.get('status')}")
        data = query_result.get('data', {})
        result_type = data.get('resultType')
        results = data.get('result', [])
        print(f"Result type: {result_type}")
        print(f"Found {len(results)} series")
        
        if results:
            for i, result in enumerate(results[:5]):  # Show first 5 results only
                print(f"  Series {i+1}:")
                print(f"    Metric: {result.get('metric')}")
                print(f"    Value: {result.get('value')}")
    except Exception as e:
        print(f"Query failed: {e}")
    
    # Memory metric queries
    print("\n2. Testing memory metric queries...")
    
    # Current memory usage percentage
    try:
        print("\n2.1 Current memory usage percentage:")
        query = "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100"
        query_result = mcp.prometheus_query(query)
        
        print(f"Query: {query}")
        print(f"Status: {query_result.get('status')}")
        
        data = query_result.get('data', {})
        results = data.get('result', [])
        
        if results:
            for i, result in enumerate(results[:3]):
                print(f"  Host {i+1}: {result.get('metric', {}).get('instance', 'unknown')}")
                # Value is a tuple with [timestamp, value]
                try:
                    value = float(result.get('value', [0, 0])[1])
                    print(f"    Memory usage: {value:.2f}%")
                    
                    # Add interpretation
                    if value > 90:
                        status = "CRITICAL"
                    elif value > 80:
                        status = "WARNING" 
                    elif value > 70:
                        status = "ELEVATED"
                    else:
                        status = "NORMAL"
                    
                    print(f"    Status: {status}")
                except (ValueError, TypeError, IndexError):
                    print("    Unable to parse value")
        else:
            print("  No results found. Node exporter might not be running.")
    except Exception as e:
        print(f"  Memory usage query failed: {e}")
    
    # Total memory capacity
    try:
        print("\n2.2 Total memory capacity:")
        query = "node_memory_MemTotal_bytes"
        query_result = mcp.prometheus_query(query)
        
        data = query_result.get('data', {})
        results = data.get('result', [])
        
        if results:
            for i, result in enumerate(results[:3]):
                print(f"  Host {i+1}: {result.get('metric', {}).get('instance', 'unknown')}")
                try:
                    bytes_value = float(result.get('value', [0, 0])[1])
                    gb_value = bytes_value / (1024 * 1024 * 1024)
                    print(f"    Total Memory: {gb_value:.2f} GB")
                except (ValueError, TypeError, IndexError):
                    print("    Unable to parse value")
        else:
            print("  No results found. Node exporter might not be running.")
    except Exception as e:
        print(f"  Total memory query failed: {e}")
    
    # Memory usage over time
    print("\n2.3 Memory usage over time (last 15 minutes):")
    try:
        # Calculate time range for the last 15 minutes
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=15)
        
        # Format timestamps for Prometheus
        end_str = end_time.isoformat("T") + "Z"
        start_str = start_time.isoformat("T") + "Z"
        
        # Query for memory usage percentage over time
        query = "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100"
        range_result = mcp.prometheus_query_range(
            query=query,
            start=start_str,
            end=end_str,
            step="60s"  # 1-minute intervals
        )
        
        print(f"Query: {query}")
        print(f"Status: {range_result.get('status')}")
        
        data = range_result.get('data', {})
        results = data.get('result', [])
        
        if results:
            for i, result in enumerate(results[:2]):
                print(f"  Host {i+1}: {result.get('metric', {}).get('instance', 'unknown')}")
                values = result.get('values', [])
                
                if values:
                    print(f"    Data points: {len(values)}")
                    
                    # Calculate average, min, max
                    try:
                        value_points = [float(v[1]) for v in values]
                        avg_value = sum(value_points) / len(value_points)
                        min_value = min(value_points)
                        max_value = max(value_points)
                        
                        print(f"    Average memory usage: {avg_value:.2f}%")
                        print(f"    Minimum memory usage: {min_value:.2f}%")
                        print(f"    Maximum memory usage: {max_value:.2f}%")
                        
                        # Memory usage trend
                        if len(value_points) > 1:
                            first_value = value_points[0]
                            last_value = value_points[-1]
                            
                            if last_value > first_value * 1.1:  # 10% increase
                                trend = "INCREASING"
                            elif last_value < first_value * 0.9:  # 10% decrease
                                trend = "DECREASING"
                            else:
                                trend = "STABLE"
                                
                            print(f"    Memory usage trend: {trend}")
                    except (ValueError, TypeError, IndexError) as e:
                        print(f"    Error calculating statistics: {e}")
                else:
                    print("    No data points found in the time range")
        else:
            print("  No results found. Node exporter might not be running.")
    except Exception as e:
        print(f"  Memory range query failed: {e}")
    
    # Check for memory-related alerts
    print("\n3. Checking memory alerts...")
    try:
        # First check if there are any active memory alerts
        alerts_result = mcp.prometheus_get_alerts()
        
        data = alerts_result.get('data', {})
        all_alerts = data.get('alerts', [])
        
        # Filter for memory-related alerts - including both node and container alerts
        memory_alerts = [
            alert for alert in all_alerts 
            if 'alertname' in alert.get('labels', {}) and 
            any(memory_term in alert.get('labels', {}).get('alertname', '').lower() 
                for memory_term in ['memory', 'mem', 'swap', 'container'])
        ]
        
        print(f"Found {len(memory_alerts)} memory-related alerts out of {len(all_alerts)} total alerts")
        
        if memory_alerts:
            # Group alerts by type
            node_memory_alerts = []
            container_memory_alerts = []
            
            for alert in memory_alerts:
                alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
                
                # Check if this is a container alert
                if 'container' in alert_name.lower() or 'name' in alert.get('labels', {}):
                    container_memory_alerts.append(alert)
                else:
                    node_memory_alerts.append(alert)
            
            # Get AI recommendations for alerts
            if node_memory_alerts or container_memory_alerts:
                ai_recommendations = get_ai_recommendations(mcp, node_memory_alerts, container_memory_alerts)
                
                print("\n=== AI-ASSISTED ANALYSIS AND RECOMMENDATIONS ===")
                print(ai_recommendations)
                print("===================================================")
            
            # Display node memory alerts
            if node_memory_alerts:
                print("\n  Node Memory Alerts:")
                for i, alert in enumerate(node_memory_alerts):
                    alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
                    severity = alert.get('labels', {}).get('severity', 'unknown')
                    state = alert.get('state', 'unknown')
                    instance = alert.get('labels', {}).get('instance', 'unknown')
                    summary = alert.get('annotations', {}).get('summary', 'No summary available')
                    
                    print(f"  Alert {i+1}: {alert_name}")
                    print(f"    Instance: {instance}")
                    print(f"    Severity: {severity}")
                    print(f"    State: {state}")
                    print(f"    Summary: {summary}")
                    
                    # For firing alerts, recommend actions
                    if state.lower() == 'firing':
                        if 'high' in alert_name.lower():
                            print("    Recommended action: Consider freeing up memory or increasing capacity")
                        elif 'critical' in alert_name.lower():
                            print("    Recommended action: Immediately free up memory, potential system instability")
                        elif 'medium' in alert_name.lower():
                            print("    Recommended action: Monitor memory usage trends")
                        elif 'low' in alert_name.lower():
                            print("    Recommended action: Normal operations, no action needed")
                        elif 'swap' in alert_name.lower():
                            print("    Recommended action: Increase swap space or reduce memory pressure")
            
            # Display container memory alerts
            if container_memory_alerts:
                print("\n  Container Memory Alerts:")
                for i, alert in enumerate(container_memory_alerts):
                    alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
                    severity = alert.get('labels', {}).get('severity', 'unknown')
                    state = alert.get('state', 'unknown')
                    
                    # Get container information
                    container_name = alert.get('labels', {}).get('name', 
                                     alert.get('labels', {}).get('container_name', 'unknown'))
                    
                    summary = alert.get('annotations', {}).get('summary', 'No summary available')
                    
                    print(f"  Alert {i+1}: {alert_name}")
                    print(f"    Container: {container_name}")
                    print(f"    Severity: {severity}")
                    print(f"    State: {state}")
                    print(f"    Summary: {summary}")
                    
                    # For firing alerts, recommend actions specific to containers
                    if state.lower() == 'firing':
                        print("    Recommended actions:")
                        print("      - Increase container memory limit")
                        print("      - Optimize container application memory usage")
                        print("      - Check for memory leaks in the container application")
                        print("      - Consider scaling horizontally instead of vertically")
                
                # Query container memory usage
                try:
                    print("\n  Current Container Memory Usage:")
                    
                    query = 'container_memory_usage_bytes{container_name!=""}'
                    mem_usage_result = mcp.prometheus_query(query)
                    
                    query_limit = 'container_spec_memory_limit_bytes{container_name!=""}'
                    mem_limit_result = mcp.prometheus_query(query_limit)
                    
                    usage_data = mem_usage_result.get('data', {}).get('result', [])
                    limit_data = mem_limit_result.get('data', {}).get('result', [])
                    
                    if usage_data and limit_data:
                        for result in usage_data:
                            container = result.get('metric', {}).get('container_name', 'unknown')
                            
                            # Skip pause containers and empty names
                            if container in ['', 'POD', 'pause'] or not container:
                                continue
                                
                            try:
                                # Get memory usage in bytes
                                memory_bytes = float(result.get('value', [0, 0])[1])
                                memory_mb = memory_bytes / (1024 * 1024)
                                
                                # Find memory limit for this container
                                memory_limit_bytes = next(
                                    (float(r.get('value', [0, 0])[1]) 
                                     for r in limit_data 
                                     if r.get('metric', {}).get('container_name') == container),
                                    float('inf')
                                )
                                
                                # Handle unlimited containers
                                if memory_limit_bytes == float('inf') or memory_limit_bytes == 0:
                                    print(f"    Container '{container}': {memory_mb:.2f} MB (no limit set)")
                                    continue
                                    
                                memory_limit_mb = memory_limit_bytes / (1024 * 1024)
                                usage_percent = (memory_bytes / memory_limit_bytes) * 100
                                
                                # Determine status
                                if usage_percent > 80:
                                    status = "CRITICAL"
                                elif usage_percent > 60:
                                    status = "WARNING"
                                elif usage_percent > 40:
                                    status = "ELEVATED"
                                else:
                                    status = "NORMAL"
                                
                                print(f"    Container '{container}': {memory_mb:.2f} MB / {memory_limit_mb:.2f} MB ({usage_percent:.1f}%) - {status}")
                            except (ValueError, TypeError, ZeroDivisionError) as e:
                                print(f"    Container '{container}': Error processing data - {e}")
                    else:
                        print("    No container memory data available")
                except Exception as e:
                    print(f"    Error querying container memory: {e}")
        else:
            print("  No memory-related alerts found.")
            
            # Create sample/demo alerts if no real ones exist
            print("\n  Demo memory alerts (for testing):")
            print("  Alert 1: HighMemoryUsage")
            print("    Severity: warning")
            print("    State: firing")
            print("    Summary: High memory usage on demo-host-1")
            print("    Memory usage: 87.5%")
            print("    Recommended action: Free up memory by stopping unnecessary processes")
            
            print("\n  Alert 2: CriticalMemoryUsage")
            print("    Severity: critical")
            print("    State: firing")
            print("    Summary: Critical memory usage on demo-host-2")
            print("    Memory usage: 96.3%")
            print("    Recommended action: Immediately add memory or stop critical processes")
            
            print("\n  Alert 3: SwapUsageHigh")
            print("    Severity: warning")
            print("    State: pending")
            print("    Summary: High swap usage on demo-host-3")
            print("    Swap usage: 82.7%")
            print("    Recommended action: Increase swap space or reduce memory consumption")
    except Exception as e:
        print(f"  Alerts query failed: {e}")
        
        # Show dummy alerts if the query failed
        print("\n  Demo memory alerts (query failed):")
        print("  Alert 1: HighMemoryUsage (Demo)")
        print("    Severity: warning")
        print("    State: firing")
        print("    Summary: High memory usage on demo-host")
        print("    Recommended action: Free up memory by stopping unnecessary processes")
    
    # Generate a memory health report
    print("\n4. Memory health report:")
    try:
        # Query current memory metrics
        mem_total_result = mcp.prometheus_query("node_memory_MemTotal_bytes")
        mem_available_result = mcp.prometheus_query("node_memory_MemAvailable_bytes")
        mem_usage_pct_result = mcp.prometheus_query("(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100")
        
        # Check results and generate report
        mem_total_data = mem_total_result.get('data', {}).get('result', [])
        mem_available_data = mem_available_result.get('data', {}).get('result', [])
        mem_usage_pct_data = mem_usage_pct_result.get('data', {}).get('result', [])
        
        if mem_total_data and mem_available_data and mem_usage_pct_data:
            print("  Memory Health Report (actual data):")
            
            # Process each host
            for i, result in enumerate(mem_usage_pct_data[:3]):
                instance = result.get('metric', {}).get('instance', f'host-{i+1}')
                
                # Get memory usage percentage
                try:
                    mem_usage_pct = float(result.get('value', [0, 0])[1])
                    
                    # Find corresponding total memory value
                    mem_total = next(
                        (float(r.get('value', [0, 0])[1]) for r in mem_total_data 
                         if r.get('metric', {}).get('instance') == instance),
                        0
                    )
                    
                    # Find corresponding available memory value
                    mem_available = next(
                        (float(r.get('value', [0, 0])[1]) for r in mem_available_data 
                         if r.get('metric', {}).get('instance') == instance),
                        0
                    )
                    
                    # Convert to GB for readability
                    mem_total_gb = mem_total / (1024 * 1024 * 1024)
                    mem_available_gb = mem_available / (1024 * 1024 * 1024)
                    mem_used_gb = mem_total_gb - mem_available_gb
                    
                    print(f"\n  Host: {instance}")
                    print(f"    Total Memory: {mem_total_gb:.2f} GB")
                    print(f"    Used Memory: {mem_used_gb:.2f} GB")
                    print(f"    Available Memory: {mem_available_gb:.2f} GB")
                    print(f"    Memory Usage: {mem_usage_pct:.2f}%")
                    
                    # Memory health status
                    if mem_usage_pct > 90:
                        status = "CRITICAL - Immediate action required"
                    elif mem_usage_pct > 80:
                        status = "WARNING - High memory usage"
                    elif mem_usage_pct > 70:
                        status = "ATTENTION - Elevated memory usage"
                    else:
                        status = "HEALTHY - Normal memory usage"
                    
                    print(f"    Status: {status}")
                    
                    # Recommendations
                    print("    Recommendations:")
                    if mem_usage_pct > 90:
                        print("     - Immediately free up memory by stopping non-critical processes")
                        print("     - Consider adding additional memory capacity")
                        print("     - Check for memory leaks in applications")
                    elif mem_usage_pct > 80:
                        print("     - Monitor memory usage closely")
                        print("     - Plan for potential memory expansion")
                        print("     - Optimize memory-intensive applications")
                    elif mem_usage_pct > 70:
                        print("     - Review memory usage trends")
                        print("     - Identify memory-intensive applications")
                    else:
                        print("     - Continue regular monitoring")
                except (ValueError, TypeError, IndexError) as e:
                    print(f"    Error processing data: {e}")
        else:
            # Generate demo report if no real data
            print("  Memory Health Report (demo data):")
            
            hosts = [
                {
                    "name": "demo-host-1",
                    "total_gb": 16.0,
                    "usage_pct": 85.6,
                    "status": "WARNING"
                },
                {
                    "name": "demo-host-2",
                    "total_gb": 32.0,
                    "usage_pct": 62.4,
                    "status": "HEALTHY"
                },
                {
                    "name": "demo-host-3",
                    "total_gb": 8.0,
                    "usage_pct": 93.2,
                    "status": "CRITICAL"
                }
            ]
            
            for host in hosts:
                name = host["name"]
                total_gb = host["total_gb"]
                usage_pct = host["usage_pct"]
                status = host["status"]
                
                used_gb = total_gb * (usage_pct / 100)
                available_gb = total_gb - used_gb
                
                print(f"\n  Host: {name}")
                print(f"    Total Memory: {total_gb:.2f} GB")
                print(f"    Used Memory: {used_gb:.2f} GB")
                print(f"    Available Memory: {available_gb:.2f} GB")
                print(f"    Memory Usage: {usage_pct:.2f}%")
                print(f"    Status: {status}")
                
                print("    Recommendations:")
                if status == "CRITICAL":
                    print("     - Immediately free up memory by stopping non-critical processes")
                    print("     - Consider adding additional memory capacity")
                    print("     - Check for memory leaks in applications")
                elif status == "WARNING":
                    print("     - Monitor memory usage closely")
                    print("     - Plan for potential memory expansion")
                    print("     - Optimize memory-intensive applications")
                else:
                    print("     - Continue regular monitoring")
    except Exception as e:
        print(f"  Memory report generation failed: {e}")
        
        # Show demo report if query failed
        print("  Memory Health Report (demo data - error fallback):")
        print("  Host: demo-host-fallback")
        print("    Total Memory: 16.00 GB")
        print("    Used Memory: 13.60 GB")
        print("    Available Memory: 2.40 GB")
        print("    Memory Usage: 85.00%")
        print("    Status: WARNING - High memory usage")
        print("    Recommendations:")
        print("     - Monitor memory usage closely")
        print("     - Plan for potential memory expansion")
        print("     - Optimize memory-intensive applications")
    
    print("\nPrometheus memory monitoring test completed.")

def get_ai_recommendations(mcp, node_alerts, container_alerts):
    """Get AI-powered recommendations for memory alerts"""
    try:
        # Skip if no model with chat capability is available
        available_models = mcp.list_models()
        
        # List available chat models for debugging
        chat_models = [model for model in available_models 
                      if any(cap == "chat" for cap in model.get('capabilities', []))]
        
        print("\nAvailable chat models for recommendations:")
        for model in chat_models:
            print(f"  - {model['id']}")
        
        if not chat_models:
            return "No AI models with chat capability available for recommendations."
        
        # Get preferred model from environment
        preferred_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        print(f"Preferred model from environment: {preferred_model}")
        
        # First try to find exact model ID match
        model_id = None
        for model in chat_models:
            if model['id'] == preferred_model:
                model_id = model['id']
                print(f"Using exact match model: {model_id}")
                break
                
        # Then try to find model containing the preferred name
        if not model_id:
            for model in chat_models:
                if preferred_model.lower() in model['id'].lower():
                    model_id = model['id']
                    print(f"Using partial match model: {model_id}")
                    break
        
        # Then try to find any OpenAI model
        if not model_id:
            for model in chat_models:
                if "openai" in model['id'].lower():
                    model_id = model['id']
                    print(f"Using OpenAI model: {model_id}")
                    break
        
        # If still no model found, use the first available
        if not model_id:
            model_id = chat_models[0]['id']
            print(f"Using first available model: {model_id}")
        
        # Format memory alert information for the AI
        node_alert_text = ""
        if node_alerts:
            node_alert_text = "Host Memory Alerts:\n"
            for i, alert in enumerate(node_alerts):
                alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
                severity = alert.get('labels', {}).get('severity', 'unknown')
                state = alert.get('state', 'unknown')
                instance = alert.get('labels', {}).get('instance', 'unknown')
                summary = alert.get('annotations', {}).get('summary', 'No summary available')
                
                node_alert_text += f"- Alert {i+1}: {alert_name}\n"
                node_alert_text += f"  Instance: {instance}\n"
                node_alert_text += f"  Severity: {severity}\n"
                node_alert_text += f"  State: {state}\n"
                node_alert_text += f"  Summary: {summary}\n\n"
        
        container_alert_text = ""
        if container_alerts:
            container_alert_text = "Container Memory Alerts:\n"
            for i, alert in enumerate(container_alerts):
                alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
                severity = alert.get('labels', {}).get('severity', 'unknown')
                state = alert.get('state', 'unknown')
                container_name = alert.get('labels', {}).get('name', 
                                alert.get('labels', {}).get('container_name', 'unknown'))
                summary = alert.get('annotations', {}).get('summary', 'No summary available')
                
                container_alert_text += f"- Alert {i+1}: {alert_name}\n"
                container_alert_text += f"  Container: {container_name}\n"
                container_alert_text += f"  Severity: {severity}\n"
                container_alert_text += f"  State: {state}\n"
                container_alert_text += f"  Summary: {summary}\n\n"
        
        # Create the prompt for the AI
        prompt = f"""
        I need expert advice on handling the following memory alerts from Prometheus monitoring:
        
        {node_alert_text}
        {container_alert_text}
        
        Please provide:
        1. A brief analysis of what these alerts indicate
        2. Detailed technical recommendations for addressing each issue
        3. Potential long-term solutions to prevent these issues from recurring
        4. Any relevant commands or actions that might help diagnose or fix the problems
        
        Keep your response focused, technical, and actionable.
        """
        
        # Query the AI model
        print(f"\nQuerying AI model ({model_id}) for recommendations...")
        
        # Prepare messages for chat
        messages = [
            {"role": "system", "content": "You are an expert systems administrator specializing in memory management, performance optimization, and containerization technologies."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Make the API call
            response = mcp.process(
                input_type="chat",
                model_id=model_id,
                messages=messages,
                max_tokens=1000
            )
            
            # Extract the response content
            if isinstance(response, dict) and 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content']
                return content
            else:
                print(f"Unexpected response format: {response}")
                return "AI recommendation failed: Could not parse response from the model."
        except Exception as e:
            print(f"Error querying AI model: {e}")
            return f"AI recommendation failed: {str(e)}\n\nFallback Recommendations:\n"\
                   "- For host memory issues: Check running processes with 'top' or 'htop'\n"\
                   "- For container memory issues: Consider increasing container memory limits\n"\
                   "- Monitor memory usage trends to identify patterns\n"\
                   "- Consider implementing memory limits or quotas"
    
    except Exception as e:
        return f"AI recommendation failed: {str(e)}\n\nFallback Recommendations:\n"\
               "- For host memory issues: Check running processes with 'top' or 'htop'\n"\
               "- For container memory issues: Consider increasing container memory limits\n"\
               "- Monitor memory usage trends to identify patterns\n"\
               "- Consider implementing memory limits or quotas"

if __name__ == "__main__":
    prometheus_url = None
    if len(sys.argv) > 1:
        prometheus_url = sys.argv[1]
    
    test_prometheus(prometheus_url) 