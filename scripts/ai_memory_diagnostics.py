#!/usr/bin/env python3
"""
AI-powered Memory Diagnostics - Uses MCP and AI to analyze Prometheus memory alerts
and provide detailed technical recommendations.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import the MCP client
from langflow import MCPAIComponent

class MemoryDiagnostics:
    """AI-powered memory diagnostics using Prometheus and MCP"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000", 
                 prometheus_url: str = "http://localhost:9090",
                 ai_model_id: str = None):
        """Initialize the diagnostics
        
        Args:
            mcp_server_url: URL of the MCP server
            prometheus_url: URL of the Prometheus server
            ai_model_id: ID of the AI model to use for analysis (or auto-select if None)
        """
        self.mcp_server_url = mcp_server_url
        self.prometheus_url = prometheus_url
        self.ai_model_id = ai_model_id
        self.mcp = MCPAIComponent(mcp_server_url=mcp_server_url)
        
        # Set the Prometheus URL in the environment
        os.environ["PROMETHEUS_URL"] = prometheus_url
        
        # Auto-select AI model if not specified
        if not self.ai_model_id:
            self._select_ai_model()
    
    def _select_ai_model(self):
        """Auto-select an appropriate AI model"""
        try:
            # Get available models
            models = self.mcp.list_models()
            chat_models = [model for model in models 
                          if any(cap == "chat" for cap in model.get('capabilities', []))]
            
            # Print all available models for debugging
            print("\nAvailable chat models:")
            for model in chat_models:
                print(f"  - {model['id']} ({', '.join(model.get('capabilities', []))})")
            print()
            
            if not chat_models:
                print("Warning: No chat-capable AI models found")
                self.ai_model_id = None
                return
            
            # Get preferred model from environment
            preferred_chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
            print(f"Preferred model from environment: {preferred_chat_model}")
            
            # Look for models in order of preference
            
            # First check for exact matching model ID
            for model in chat_models:
                if model['id'].lower() == preferred_chat_model.lower():
                    self.ai_model_id = model['id']
                    print(f"Selected AI model (exact match): {self.ai_model_id}")
                    return
            
            # Then check for models containing the preferred name
            for model in chat_models:
                if preferred_chat_model.lower() in model['id'].lower():
                    self.ai_model_id = model['id']
                    print(f"Selected AI model (partial match): {self.ai_model_id}")
                    return
            
            # Then look for any OpenAI model
            for model in chat_models:
                if "openai" in model['id'].lower():
                    self.ai_model_id = model['id']
                    print(f"Selected AI model (OpenAI): {self.ai_model_id}")
                    return
            
            # Prefer more advanced models (GPT-4 > Claude > GPT-3.5)
            for model_name_part in ["gpt-4", "claude", "gpt-3.5", "gpt"]:
                for model in chat_models:
                    if model_name_part in model['id'].lower():
                        self.ai_model_id = model['id']
                        print(f"Selected AI model (by type): {self.ai_model_id}")
                        return
            
            # If no preference matches, use the first one
            self.ai_model_id = chat_models[0]['id']
            print(f"Selected AI model (first available): {self.ai_model_id}")
        except Exception as e:
            print(f"Warning: Error selecting AI model: {e}")
            print("Falling back to basic analysis without AI")
            self.ai_model_id = None
    
    def fetch_alerts(self) -> List[Dict[str, Any]]:
        """Fetch memory-related alerts from Prometheus"""
        try:
            alerts_result = self.mcp.prometheus_get_alerts()
            
            if alerts_result.get('status') == 'success':
                all_alerts = alerts_result.get('data', {}).get('alerts', [])
                
                # Filter for memory-related alerts
                memory_alerts = [
                    alert for alert in all_alerts 
                    if 'alertname' in alert.get('labels', {}) and 
                    any(term in alert.get('labels', {}).get('alertname', '').lower() 
                        for term in ['memory', 'mem', 'swap', 'container'])
                ]
                
                # Format alerts for display
                formatted_alerts = []
                for alert in memory_alerts:
                    alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
                    severity = alert.get('labels', {}).get('severity', 'unknown')
                    state = alert.get('state', 'unknown')
                    
                    # Get target (container or instance)
                    if 'container' in alert_name.lower() or 'name' in alert.get('labels', {}):
                        target = alert.get('labels', {}).get('name', 
                                 alert.get('labels', {}).get('container_name', 'unknown'))
                        target_type = "container"
                    else:
                        target = alert.get('labels', {}).get('instance', 'unknown')
                        target_type = "host"
                    
                    summary = alert.get('annotations', {}).get('summary', 'No summary available')
                    description = alert.get('annotations', {}).get('description', '')
                    
                    formatted_alerts.append({
                        "name": alert_name,
                        "severity": severity,
                        "state": state,
                        "target": target,
                        "target_type": target_type,
                        "summary": summary,
                        "description": description
                    })
                
                return formatted_alerts
            else:
                print(f"Error fetching alerts: {alerts_result.get('error', 'Unknown error')}")
                return []
        except Exception as e:
            print(f"Exception fetching alerts: {str(e)}")
            return []
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive memory metrics"""
        metrics = {
            "system": {},
            "containers": {}
        }
        
        try:
            # System memory metrics
            # Total memory
            total_mem_result = self.mcp.prometheus_query("node_memory_MemTotal_bytes")
            
            # Available memory
            avail_mem_result = self.mcp.prometheus_query("node_memory_MemAvailable_bytes")
            
            # Memory usage percent
            usage_pct_result = self.mcp.prometheus_query(
                "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100"
            )
            
            # Process results
            if usage_pct_result.get('status') == 'success':
                results = usage_pct_result.get('data', {}).get('result', [])
                
                for result in results:
                    instance = result.get('metric', {}).get('instance', 'unknown')
                    
                    try:
                        usage_pct = float(result.get('value', [0, 0])[1])
                        
                        # Find matching total and available memory
                        total_result = next(
                            (r for r in total_mem_result.get('data', {}).get('result', [])
                             if r.get('metric', {}).get('instance') == instance),
                            None
                        )
                        
                        avail_result = next(
                            (r for r in avail_mem_result.get('data', {}).get('result', [])
                             if r.get('metric', {}).get('instance') == instance),
                            None
                        )
                        
                        if total_result and avail_result:
                            total_bytes = float(total_result.get('value', [0, 0])[1])
                            avail_bytes = float(avail_result.get('value', [0, 0])[1])
                            
                            metrics["system"][instance] = {
                                "total_bytes": total_bytes,
                                "total_gb": total_bytes / (1024 * 1024 * 1024),
                                "available_bytes": avail_bytes,
                                "available_gb": avail_bytes / (1024 * 1024 * 1024),
                                "used_bytes": total_bytes - avail_bytes,
                                "used_gb": (total_bytes - avail_bytes) / (1024 * 1024 * 1024),
                                "usage_percent": usage_pct
                            }
                    except (ValueError, TypeError, IndexError) as e:
                        print(f"Error processing memory data for {instance}: {e}")
            
            # Container memory metrics
            # Memory usage
            container_mem_result = self.mcp.prometheus_query('container_memory_usage_bytes{container_name!=""}')
            
            # Memory limits
            container_limit_result = self.mcp.prometheus_query('container_spec_memory_limit_bytes{container_name!=""}')
            
            if container_mem_result.get('status') == 'success':
                results = container_mem_result.get('data', {}).get('result', [])
                
                for result in results:
                    container = result.get('metric', {}).get('container_name', 'unknown')
                    
                    # Skip pause containers
                    if container in ['', 'POD', 'pause'] or not container:
                        continue
                    
                    try:
                        memory_bytes = float(result.get('value', [0, 0])[1])
                        
                        # Find matching limit
                        limit_result = next(
                            (r for r in container_limit_result.get('data', {}).get('result', [])
                             if r.get('metric', {}).get('container_name') == container),
                            None
                        )
                        
                        limit_bytes = 0
                        usage_percent = 0
                        
                        if limit_result:
                            limit_bytes = float(limit_result.get('value', [0, 0])[1])
                            if limit_bytes > 0:
                                usage_percent = (memory_bytes / limit_bytes) * 100
                        
                        metrics["containers"][container] = {
                            "memory_bytes": memory_bytes,
                            "memory_mb": memory_bytes / (1024 * 1024),
                            "limit_bytes": limit_bytes if limit_bytes > 0 else None,
                            "limit_mb": limit_bytes / (1024 * 1024) if limit_bytes > 0 else None,
                            "usage_percent": usage_percent
                        }
                    except (ValueError, TypeError, IndexError) as e:
                        print(f"Error processing container memory data for {container}: {e}")
            
            return metrics
        except Exception as e:
            print(f"Error collecting memory metrics: {e}")
            return metrics
    
    def get_historical_trends(self, lookback_hours: int = 3) -> Dict[str, Any]:
        """Get historical memory usage trends"""
        trends = {
            "system": {},
            "containers": {}
        }
        
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=lookback_hours)
            
            # Format timestamps for Prometheus
            end_str = end_time.isoformat("T") + "Z"
            start_str = start_time.isoformat("T") + "Z"
            
            # Get system memory trends
            query = "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100"
            range_result = self.mcp.prometheus_query_range(
                query=query,
                start=start_str,
                end=end_str,
                step="5m"  # 5-minute intervals
            )
            
            if range_result.get('status') == 'success':
                results = range_result.get('data', {}).get('result', [])
                
                for result in results:
                    instance = result.get('metric', {}).get('instance', 'unknown')
                    values = result.get('values', [])
                    
                    if values:
                        # Process trend data - get min, max, avg, trend direction
                        try:
                            timestamps = [v[0] for v in values]
                            data_points = [float(v[1]) for v in values]
                            
                            trends["system"][instance] = {
                                "min": min(data_points),
                                "max": max(data_points),
                                "avg": sum(data_points) / len(data_points),
                                "trend": "increasing" if data_points[-1] > data_points[0] else "decreasing" if data_points[-1] < data_points[0] else "stable",
                                "samples": len(data_points),
                                "time_range": f"{lookback_hours} hours"
                            }
                        except (ValueError, TypeError, IndexError) as e:
                            print(f"Error processing system trend data for {instance}: {e}")
            
            # Get container memory trends for selected containers
            for container in list(self.get_memory_metrics()["containers"].keys())[:5]:  # Limit to 5 containers
                query = f'container_memory_usage_bytes{{container_name="{container}"}}'
                
                range_result = self.mcp.prometheus_query_range(
                    query=query,
                    start=start_str,
                    end=end_str,
                    step="5m"  # 5-minute intervals
                )
                
                if range_result.get('status') == 'success':
                    results = range_result.get('data', {}).get('result', [])
                    
                    for result in results:
                        values = result.get('values', [])
                        
                        if values:
                            # Process trend data
                            try:
                                timestamps = [v[0] for v in values]
                                data_points = [float(v[1]) / (1024 * 1024) for v in values]  # Convert to MB
                                
                                trends["containers"][container] = {
                                    "min_mb": min(data_points),
                                    "max_mb": max(data_points),
                                    "avg_mb": sum(data_points) / len(data_points),
                                    "trend": "increasing" if data_points[-1] > data_points[0] else "decreasing" if data_points[-1] < data_points[0] else "stable",
                                    "samples": len(data_points),
                                    "time_range": f"{lookback_hours} hours"
                                }
                            except (ValueError, TypeError, IndexError) as e:
                                print(f"Error processing container trend data for {container}: {e}")
            
            return trends
        except Exception as e:
            print(f"Error collecting trend data: {e}")
            return trends
    
    def get_ai_analysis(self, alerts, metrics, trends, detailed=False) -> str:
        """Get AI analysis of memory metrics and alerts"""
        if not self.ai_model_id:
            return "No AI model available for analysis."
        
        try:
            # Format alerts for the prompt
            alert_text = ""
            if alerts:
                alert_text = "Current Memory Alerts:\n"
                for i, alert in enumerate(alerts):
                    alert_text += f"- {alert['name']} ({alert['severity']})\n"
                    alert_text += f"  Target: {alert['target']} ({alert['target_type']})\n"
                    alert_text += f"  State: {alert['state']}\n"
                    alert_text += f"  Summary: {alert['summary']}\n\n"
            else:
                alert_text = "No active memory alerts.\n\n"
            
            # Format metrics for the prompt
            metric_text = "Current Memory Metrics:\n"
            
            # System metrics
            for instance, data in metrics["system"].items():
                metric_text += f"Host: {instance}\n"
                metric_text += f"- Total Memory: {data.get('total_gb', 0):.2f} GB\n"
                metric_text += f"- Used Memory: {data.get('used_gb', 0):.2f} GB\n"
                metric_text += f"- Available Memory: {data.get('available_gb', 0):.2f} GB\n"
                metric_text += f"- Usage: {data.get('usage_percent', 0):.1f}%\n\n"
            
            # Container metrics (top 5 by usage)
            sorted_containers = sorted(
                metrics["containers"].items(),
                key=lambda x: x[1].get("usage_percent", 0),
                reverse=True
            )
            
            if sorted_containers:
                metric_text += "Top Containers by Memory Usage:\n"
                for container, data in sorted_containers[:5]:
                    memory_mb = data.get("memory_mb", 0)
                    limit_text = f" / {data.get('limit_mb', 0):.2f} MB ({data.get('usage_percent', 0):.1f}%)" if data.get("limit_mb") else " (no limit)"
                    metric_text += f"- {container}: {memory_mb:.2f} MB{limit_text}\n"
            
            # Format trends for the prompt
            trend_text = "\nMemory Usage Trends:\n"
            
            # System trends
            for instance, data in trends["system"].items():
                trend_text += f"Host: {instance}\n"
                trend_text += f"- Trend: {data.get('trend', 'unknown').upper()}\n"
                trend_text += f"- Min: {data.get('min', 0):.1f}%, Max: {data.get('max', 0):.1f}%, Avg: {data.get('avg', 0):.1f}%\n"
                trend_text += f"- Time Range: {data.get('time_range', 'unknown')}\n\n"
            
            # Container trends
            if trends["containers"]:
                trend_text += "Container Trends:\n"
                for container, data in trends["containers"].items():
                    trend_text += f"- {container}: {data.get('trend', 'unknown').upper()}, "
                    trend_text += f"Min: {data.get('min_mb', 0):.2f} MB, "
                    trend_text += f"Max: {data.get('max_mb', 0):.2f} MB, "
                    trend_text += f"Avg: {data.get('avg_mb', 0):.2f} MB\n"
            
            # Create the prompt
            if detailed:
                prompt = f"""
                I need a detailed expert analysis of the memory situation in a system being monitored by Prometheus.
                
                {alert_text}
                
                {metric_text}
                
                {trend_text}
                
                Please provide:
                1. A detailed technical analysis of the current memory situation
                2. Specific recommendations for addressing any issues, including exact commands where appropriate
                3. Potential root causes of any memory problems detected
                4. Long-term strategies for memory optimization
                5. If no immediate issues are detected, preventative measures and best practices
                
                Focus on being technical, detailed, and practical.
                """
            else:
                prompt = f"""
                Analyze the following memory metrics and alerts from a system being monitored by Prometheus.
                
                {alert_text}
                
                {metric_text}
                
                {trend_text}
                
                Please provide a concise analysis including:
                1. Summary of the current memory situation
                2. Key recommendations to address any issues
                3. Brief assessment of memory usage trends
                
                Keep the response short and actionable.
                """
            
            # Prepare system prompt based on whether there are alerts
            if alerts:
                system_prompt = "You are an expert systems administrator specializing in memory management and performance troubleshooting. You provide technical, accurate, and actionable advice for resolving memory issues."
            else:
                system_prompt = "You are an expert systems administrator specializing in memory management. You provide concise technical advice on memory optimization and preventative measures."
            
            # Prepare messages for chat
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Get token limit based on model
            max_tokens = 1000
            if "gpt-4" in self.ai_model_id.lower():
                max_tokens = 2000
            
            # Handle different model types
            print(f"Querying model {self.ai_model_id}...")
            
            try:
                # Make the API call
                response = self.mcp.process(
                    input_type="chat",
                    model_id=self.ai_model_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.3  # Lower temperature for more focused responses
                )
                
                # Extract the response content
                if isinstance(response, dict):
                    if 'choices' in response and len(response['choices']) > 0:
                        content = response['choices'][0]['message']['content']
                        return content
                    elif 'error' in response:
                        return f"AI analysis failed: {response['error']}"
                    else:
                        # Try to find content in other response formats
                        for key in ['text', 'content', 'message']:
                            if key in response:
                                return response[key]
                return "AI analysis failed: Unexpected response format"
            except Exception as inner_e:
                print(f"Error during model query: {inner_e}")
                
                # Try fallback to openai model if azure fails
                if "azure" in self.ai_model_id.lower():
                    try:
                        print("Trying fallback to OpenAI model...")
                        fallback_model_id = f"openai-{os.getenv('OPENAI_CHAT_MODEL', 'gpt-4o-mini')}"
                        
                        response = self.mcp.process(
                            input_type="chat",
                            model_id=fallback_model_id,
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=0.3
                        )
                        
                        if isinstance(response, dict) and 'choices' in response:
                            content = response['choices'][0]['message']['content']
                            return content
                    except Exception as fallback_e:
                        print(f"Fallback also failed: {fallback_e}")
                
                return f"AI analysis failed: {inner_e}"
        except Exception as e:
            return f"AI analysis failed: {str(e)}\n\nBasic Recommendations:\n"\
                   "- For host memory issues: Check running processes with 'top' or 'htop'\n"\
                   "- For container memory issues: Consider increasing container memory limits\n"\
                   "- Monitor memory usage trends to identify patterns"
    
    def run_diagnostics(self, detailed=False, lookback_hours=3) -> None:
        """Run full memory diagnostics"""
        print("\n" + "=" * 80)
        print("AI-POWERED MEMORY DIAGNOSTICS")
        print("=" * 80)
        
        # Get alerts
        print("Fetching memory alerts...")
        alerts = self.fetch_alerts()
        print(f"Found {len(alerts)} memory-related alerts")
        
        # Get current metrics
        print("Collecting current memory metrics...")
        metrics = self.get_memory_metrics()
        
        # Get historical trends
        print(f"Analyzing memory trends over the past {lookback_hours} hours...")
        trends = self.get_historical_trends(lookback_hours)
        
        # Get AI analysis
        if self.ai_model_id:
            print(f"Requesting AI analysis using model {self.ai_model_id}...")
            analysis = self.get_ai_analysis(alerts, metrics, trends, detailed)
            
            print("\n" + "=" * 80)
            print("MEMORY ANALYSIS AND RECOMMENDATIONS")
            print("=" * 80 + "\n")
            print(analysis)
        else:
            print("\nAI analysis not available - no chat model found")
            
            # Print a basic report without AI
            print("\n" + "=" * 80)
            print("BASIC MEMORY REPORT")
            print("=" * 80 + "\n")
            
            # Print alerts
            if alerts:
                print("Memory Alerts:")
                for alert in alerts:
                    print(f"- {alert['name']} ({alert['severity']}) on {alert['target']}")
                    print(f"  {alert['summary']}")
            else:
                print("No memory alerts detected.")
            
            # Print system metrics
            for instance, data in metrics["system"].items():
                print(f"\nHost: {instance}")
                print(f"Memory Usage: {data.get('usage_percent', 0):.1f}%")
                print(f"Total: {data.get('total_gb', 0):.2f} GB")
                print(f"Used: {data.get('used_gb', 0):.2f} GB")
                print(f"Available: {data.get('available_gb', 0):.2f} GB")
            
            # Basic recommendations
            print("\nBasic Recommendations:")
            if any(data.get('usage_percent', 0) > 70 for data in metrics["system"].values()):
                print("- High system memory usage detected. Consider freeing up memory.")
                print("- Check for memory leaks or runaway processes.")
            else:
                print("- System memory usage appears normal.")
                
            # Check for high container usage
            high_containers = [
                (name, data) for name, data in metrics["containers"].items()
                if data.get('usage_percent', 0) > 70
            ]
            
            if high_containers:
                print("\n- High memory usage in containers:")
                for name, data in high_containers:
                    print(f"  * {name}: {data.get('usage_percent', 0):.1f}%")
                print("- Consider increasing container memory limits or optimizing applications.")
        
        print("\n" + "=" * 80)
        print(f"Diagnostics completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AI-powered Memory Diagnostics")
    parser.add_argument("--mcp-url", default=os.getenv("MCP_SERVER_URL", "http://localhost:8000"),
                        help="MCP server URL")
    parser.add_argument("--prometheus-url", default=os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
                        help="Prometheus server URL")
    parser.add_argument("--ai-model", default=None,
                        help="Specific AI model ID to use")
    parser.add_argument("--model-type", choices=["openai", "azure"], default="openai",
                        help="Type of model to use (openai or azure)")
    parser.add_argument("--detailed", action="store_true",
                        help="Generate a detailed analysis")
    parser.add_argument("--lookback", type=int, default=3,
                        help="Hours to look back for trend analysis")
    parser.add_argument("--list-models", action="store_true",
                        help="List available AI models and exit")
    
    args = parser.parse_args()
    
    # Initialize basic client to list models if needed
    mcp = MCPAIComponent(mcp_server_url=args.mcp_url)
    
    # Just list models and exit if requested
    if args.list_models:
        models = mcp.list_models()
        print("\nAvailable AI Models:")
        print("-" * 60)
        for model in models:
            model_id = model.get('id', 'unknown')
            capabilities = ", ".join(model.get('capabilities', []))
            print(f"ID: {model_id}")
            print(f"Capabilities: {capabilities}")
            print("-" * 60)
        return
    
    # Don't try to construct a model ID, instead initialize diagnostics without a specific model
    # and let the auto-selection logic find an available one
    diagnostics = MemoryDiagnostics(
        mcp_server_url=args.mcp_url,
        prometheus_url=args.prometheus_url,
        ai_model_id=args.ai_model  # This might be None, which is fine
    )
    
    # Run diagnostics
    diagnostics.run_diagnostics(detailed=args.detailed, lookback_hours=args.lookback)

if __name__ == "__main__":
    main() 