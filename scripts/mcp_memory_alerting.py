#!/usr/bin/env python3
"""
MCP Memory Alerting - Handle and notify about Prometheus memory alerts
"""

import os
import sys
import time
import json
import argparse
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import the MCP client
from langflow import MCPAIComponent

class MemoryAlertHandler:
    """Handle memory alerts from Prometheus MCP integration"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000", 
                 prometheus_url: str = "http://localhost:9090",
                 check_interval: int = 60):
        """Initialize the alert handler
        
        Args:
            mcp_server_url: URL of the MCP server
            prometheus_url: URL of the Prometheus server
            check_interval: Alert check interval in seconds
        """
        self.mcp_server_url = mcp_server_url
        self.prometheus_url = prometheus_url
        self.check_interval = check_interval
        self.mcp = MCPAIComponent(mcp_server_url=mcp_server_url)
        
        # Set the Prometheus URL in the environment
        os.environ["PROMETHEUS_URL"] = prometheus_url
        
        # Keep track of already notified alerts
        self.notified_alerts = set()
        
        # Configuration for notification methods
        self.notification_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_addr": "alerts@example.com",
                "to_addrs": ["admin@example.com"]
            },
            "slack": {
                "enabled": False,
                "webhook_url": ""
            },
            "log": {
                "enabled": True,
                "file": "memory_alerts.log"
            },
            "system": {
                "enabled": True,  # For desktop notifications
            }
        }
    
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
                
                # Format alerts for handling
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
                    
                    # Create a unique alert ID
                    alert_id = f"{alert_name}_{target}_{severity}"
                    
                    # Format start time if available
                    starts_at = alert.get('startsAt', '')
                    if starts_at:
                        try:
                            # Parse ISO format timestamp
                            starts_at_dt = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                            formatted_time = starts_at_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                        except (ValueError, TypeError):
                            formatted_time = starts_at
                    else:
                        formatted_time = "Unknown"
                    
                    formatted_alerts.append({
                        "id": alert_id,
                        "name": alert_name,
                        "severity": severity,
                        "state": state,
                        "target": target,
                        "target_type": target_type,
                        "summary": summary,
                        "description": description,
                        "starts_at": formatted_time
                    })
                
                return formatted_alerts
            else:
                print(f"Error fetching alerts: {alerts_result.get('error', 'Unknown error')}")
                return []
        except Exception as e:
            print(f"Exception fetching alerts: {str(e)}")
            return []
    
    def get_memory_info(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Get additional memory information for an alert target"""
        try:
            target = alert["target"]
            target_type = alert["target_type"]
            
            memory_info = {}
            
            if target_type == "host":
                # Query host memory metrics
                query = f'(1 - node_memory_MemAvailable_bytes{{instance="{target}"}} / node_memory_MemTotal_bytes{{instance="{target}"}}) * 100'
                result = self.mcp.prometheus_query(query)
                
                if result.get('status') == 'success':
                    data_result = result.get('data', {}).get('result', [])
                    if data_result:
                        usage_pct = float(data_result[0].get('value', [0, '0'])[1])
                        memory_info["usage_percent"] = usage_pct
                
                # Get total memory
                query = f'node_memory_MemTotal_bytes{{instance="{target}"}}'
                result = self.mcp.prometheus_query(query)
                
                if result.get('status') == 'success':
                    data_result = result.get('data', {}).get('result', [])
                    if data_result:
                        total_bytes = float(data_result[0].get('value', [0, '0'])[1])
                        memory_info["total_gb"] = total_bytes / (1024 * 1024 * 1024)
            
            elif target_type == "container":
                # Query container memory metrics
                query = f'container_memory_usage_bytes{{container_name="{target}"}}'
                result = self.mcp.prometheus_query(query)
                
                if result.get('status') == 'success':
                    data_result = result.get('data', {}).get('result', [])
                    if data_result:
                        usage_bytes = float(data_result[0].get('value', [0, '0'])[1])
                        memory_info["usage_mb"] = usage_bytes / (1024 * 1024)
                
                # Get memory limit
                query = f'container_spec_memory_limit_bytes{{container_name="{target}"}}'
                result = self.mcp.prometheus_query(query)
                
                if result.get('status') == 'success':
                    data_result = result.get('data', {}).get('result', [])
                    if data_result:
                        limit_bytes = float(data_result[0].get('value', [0, '0'])[1])
                        if limit_bytes > 0:
                            memory_info["limit_mb"] = limit_bytes / (1024 * 1024)
                            if "usage_mb" in memory_info:
                                memory_info["usage_percent"] = (memory_info["usage_mb"] * 1024 * 1024 / limit_bytes) * 100
            
            return memory_info
        except Exception as e:
            print(f"Error getting memory info: {e}")
            return {}
    
    def format_alert_message(self, alert: Dict[str, Any], memory_info: Dict[str, Any]) -> str:
        """Format an alert for notification"""
        message = []
        message.append(f"MEMORY ALERT: {alert['name']}")
        message.append(f"Severity: {alert['severity'].upper()}")
        message.append(f"Target: {alert['target']} ({alert['target_type']})")
        message.append(f"Status: {alert['state'].upper()}")
        message.append(f"Started: {alert['starts_at']}")
        message.append(f"Summary: {alert['summary']}")
        
        if alert['description']:
            message.append(f"Description: {alert['description']}")
        
        # Add memory info
        message.append("\nCurrent Memory Details:")
        
        if alert['target_type'] == 'host':
            if 'usage_percent' in memory_info:
                message.append(f"Usage: {memory_info['usage_percent']:.1f}%")
            if 'total_gb' in memory_info:
                message.append(f"Total Memory: {memory_info['total_gb']:.2f} GB")
        
        elif alert['target_type'] == 'container':
            if 'usage_mb' in memory_info:
                message.append(f"Usage: {memory_info['usage_mb']:.2f} MB")
            if 'limit_mb' in memory_info:
                message.append(f"Limit: {memory_info['limit_mb']:.2f} MB")
            if 'usage_percent' in memory_info:
                message.append(f"Percent: {memory_info['usage_percent']:.1f}%")
        
        # Add recommendations
        message.append("\nRecommended Actions:")
        if 'high' in alert['name'].lower() or 'critical' in alert['name'].lower():
            if alert['target_type'] == 'host':
                message.append("- Investigate and stop unnecessary processes")
                message.append("- Consider adding more memory to the system")
                message.append("- Check for memory leaks in applications")
            else:  # container
                message.append("- Increase container memory limit")
                message.append("- Optimize container application memory usage")
                message.append("- Consider scaling horizontally with more containers")
        elif 'medium' in alert['name'].lower():
            message.append("- Monitor the situation for further degradation")
            message.append("- Plan for potential memory expansion")
        
        message.append(f"\nPrometheus URL: {self.prometheus_url}/alerts")
        
        return "\n".join(message)
    
    def send_email_notification(self, alert: Dict[str, Any], message: str) -> bool:
        """Send an email notification for an alert"""
        config = self.notification_config["email"]
        
        if not config["enabled"]:
            return False
        
        try:
            msg = MIMEMultipart()
            msg["From"] = config["from_addr"]
            msg["To"] = ", ".join(config["to_addrs"])
            msg["Subject"] = f"Memory Alert: {alert['name']} - {alert['severity'].upper()}"
            
            msg.attach(MIMEText(message, "plain"))
            
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls()
            
            if config["username"] and config["password"]:
                server.login(config["username"], config["password"])
            
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_slack_notification(self, alert: Dict[str, Any], message: str) -> bool:
        """Send a Slack notification for an alert"""
        config = self.notification_config["slack"]
        
        if not config["enabled"] or not config["webhook_url"]:
            return False
        
        try:
            import requests
            
            # Color based on severity
            color = {
                "critical": "#FF0000",  # Red
                "warning": "#FFA500",   # Orange
                "info": "#0000FF"       # Blue
            }.get(alert["severity"].lower(), "#808080")  # Default gray
            
            payload = {
                "attachments": [
                    {
                        "fallback": f"Memory Alert: {alert['name']}",
                        "color": color,
                        "title": f"Memory Alert: {alert['name']}",
                        "text": message.replace("\n", "\n>"),
                        "footer": "MCP Memory Alerting",
                        "ts": int(time.time())
                    }
                ]
            }
            
            response = requests.post(
                config["webhook_url"],
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Slack notification: {e}")
            return False
    
    def send_system_notification(self, alert: Dict[str, Any], message: str) -> bool:
        """Send a system notification (desktop notification)"""
        config = self.notification_config["system"]
        
        if not config["enabled"]:
            return False
        
        try:
            title = f"Memory Alert: {alert['name']} - {alert['severity'].upper()}"
            summary = f"{alert['target']} ({alert['target_type']}): {alert['summary']}"
            
            # Try different notification methods based on platform
            if sys.platform == "linux" or sys.platform == "linux2":
                # Linux: try notify-send
                subprocess.call(["notify-send", title, summary])
                return True
            elif sys.platform == "darwin":
                # macOS: try osascript
                apple_script = f'display notification "{summary}" with title "{title}"'
                subprocess.call(["osascript", "-e", apple_script])
                return True
            elif sys.platform == "win32":
                # Windows: try PowerShell
                script = f"""
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
                $app_id = 'MCP.MemoryAlertHandler'
                $content = @"
                <toast>
                    <visual>
                        <binding template="ToastText02">
                            <text id="1">{title}</text>
                            <text id="2">{summary}</text>
                        </binding>
                    </visual>
                </toast>
                "@
                $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $xml.LoadXml($content)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app_id).Show($xml)
                """
                subprocess.call(["powershell", "-Command", script])
                return True
        except Exception as e:
            print(f"Error sending system notification: {e}")
        
        return False
    
    def log_alert(self, alert: Dict[str, Any], message: str) -> bool:
        """Log an alert to a file"""
        config = self.notification_config["log"]
        
        if not config["enabled"]:
            return False
        
        try:
            log_file = config["file"]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file, "a") as f:
                f.write(f"=== ALERT LOGGED AT {timestamp} ===\n")
                f.write(message)
                f.write("\n\n")
            
            return True
        except Exception as e:
            print(f"Error logging alert: {e}")
            return False
    
    def process_alerts(self, dry_run: bool = False) -> None:
        """Process and handle alerts"""
        alerts = self.fetch_alerts()
        
        # Only process alerts in FIRING state
        firing_alerts = [a for a in alerts if a["state"].lower() == "firing"]
        
        if not firing_alerts:
            print(f"No firing alerts found at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        print(f"Found {len(firing_alerts)} firing alerts")
        
        for alert in firing_alerts:
            alert_id = alert["id"]
            
            # Skip if we've already notified about this alert
            if alert_id in self.notified_alerts:
                continue
            
            # Get additional memory information
            memory_info = self.get_memory_info(alert)
            
            # Format alert message
            message = self.format_alert_message(alert, memory_info)
            
            print(f"\nProcessing alert: {alert['name']} ({alert['severity']})")
            print(f"Target: {alert['target']} ({alert['target_type']})")
            
            if dry_run:
                print("DRY RUN - Would send notifications:")
                print(message)
            else:
                # Send notifications based on configured methods
                notification_sent = False
                
                # Log to file
                if self.log_alert(alert, message):
                    print("  - Alert logged to file")
                    notification_sent = True
                
                # Send email
                if self.notification_config["email"]["enabled"]:
                    if self.send_email_notification(alert, message):
                        print("  - Email notification sent")
                        notification_sent = True
                
                # Send Slack notification
                if self.notification_config["slack"]["enabled"]:
                    if self.send_slack_notification(alert, message):
                        print("  - Slack notification sent")
                        notification_sent = True
                
                # Send system notification
                if self.notification_config["system"]["enabled"]:
                    if self.send_system_notification(alert, message):
                        print("  - System notification sent")
                        notification_sent = True
                
                if notification_sent:
                    # Add to notified set
                    self.notified_alerts.add(alert_id)
                else:
                    print("  - No notifications sent")
    
    def run_alerting(self) -> None:
        """Run the alerting system"""
        print(f"Starting memory alert monitoring at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"MCP Server: {self.mcp_server_url}")
        print(f"Prometheus: {self.prometheus_url}")
        print(f"Check interval: {self.check_interval} seconds")
        
        try:
            while True:
                self.process_alerts()
                
                # Reset notification list after some time to allow re-notification
                # for alerts that are still firing after 1 hour
                for alert_id in list(self.notified_alerts):
                    if alert_id not in [a["id"] for a in self.fetch_alerts() if a["state"].lower() == "firing"]:
                        self.notified_alerts.remove(alert_id)
                        print(f"Alert {alert_id} resolved, removed from notification list")
                
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print("\nAlert monitoring stopped.")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MCP Memory Alerting")
    parser.add_argument("--mcp-url", default=os.getenv("MCP_SERVER_URL", "http://localhost:8000"),
                        help="MCP server URL")
    parser.add_argument("--prometheus-url", default=os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
                        help="Prometheus server URL")
    parser.add_argument("--interval", type=int, default=60,
                        help="Alert check interval in seconds")
    parser.add_argument("--log-file", default="memory_alerts.log",
                        help="Log file path")
    parser.add_argument("--email", action="store_true",
                        help="Enable email notifications")
    parser.add_argument("--email-to", 
                        help="Email recipients (comma-separated)")
    parser.add_argument("--slack", action="store_true",
                        help="Enable Slack notifications")
    parser.add_argument("--slack-webhook",
                        help="Slack webhook URL")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't send notifications, just print them")
    parser.add_argument("--once", action="store_true",
                        help="Process alerts once and exit")
    
    args = parser.parse_args()
    
    alert_handler = MemoryAlertHandler(
        mcp_server_url=args.mcp_url,
        prometheus_url=args.prometheus_url,
        check_interval=args.interval
    )
    
    # Configure notification methods
    alert_handler.notification_config["log"]["file"] = args.log_file
    
    if args.email:
        alert_handler.notification_config["email"]["enabled"] = True
        if args.email_to:
            alert_handler.notification_config["email"]["to_addrs"] = args.email_to.split(",")
    
    if args.slack:
        alert_handler.notification_config["slack"]["enabled"] = True
        if args.slack_webhook:
            alert_handler.notification_config["slack"]["webhook_url"] = args.slack_webhook
    
    if args.once:
        alert_handler.process_alerts(dry_run=args.dry_run)
    else:
        alert_handler.run_alerting()

if __name__ == "__main__":
    main() 