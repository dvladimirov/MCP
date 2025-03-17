#!/usr/bin/env python3
# MCP Formatter Component

import json
from typing import Optional, Dict, List, Any

from langflow.custom import Component
from langflow.io import DropdownInput, MessageTextInput, Output
from langflow.schema import Data
from langflow.schema.message import Message

class MCPFormatter(Component):
    """Component for formatting MCP output into beautiful reports"""
    
    # Langflow UI display properties
    display_name = "MCP Formatter"
    description = "Formats MCP analysis results into beautiful, readable reports"
    icon = "📊"
    category = "Tools"
    name = "MCPFormatter"

    # Report format options
    FORMAT_OPTIONS = [
        "markdown",          # Markdown format (works with most LLM outputs)
        "html",              # HTML format (more styling options)
        "text",              # Simple text format
    ]

    inputs = [
        MessageTextInput(
            name="json_input",
            display_name="MCP JSON Input",
            info="The JSON output from the MCP component",
            required=True
        ),
        DropdownInput(
            name="format",
            display_name="Output Format",
            info="Format for the beautified report",
            options=FORMAT_OPTIONS,
            value="markdown",
            required=True
        )
    ]

    outputs = [
        Output(display_name="Formatted Report", name="report", method="format_report"),
    ]

    def format_report(self) -> Message:
        """Format the MCP JSON output into a beautiful report"""
        # Get input data
        input_text = self.json_input.text if hasattr(self.json_input, 'text') else str(self.json_input)
        output_format = self.format
        
        try:
            # Parse JSON from input
            try:
                # First try to parse the entire input as JSON
                mcp_data = json.loads(input_text)
            except json.JSONDecodeError:
                # Try to extract JSON if wrapped in user message
                if "```json" in input_text:
                    json_str = input_text.split("```json")[1].split("```")[0].strip()
                    mcp_data = json.loads(json_str)
                else:
                    # Try to find JSON by looking for starting brace
                    lines = input_text.splitlines()
                    for i, line in enumerate(lines):
                        if line.strip().startswith("{"):
                            json_str = "\n".join(lines[i:])
                            try:
                                mcp_data = json.loads(json_str)
                                break
                            except json.JSONDecodeError:
                                continue
                    else:
                        return Message(text=f"Error: Could not parse JSON from input. Please provide valid JSON output from MCP component.\n\nReceived: {input_text[:200]}...")
            
            # Ensure we have a dictionary (some MCP responses might be strings)
            if isinstance(mcp_data, str):
                # If the MCP data is a string, try to parse it again (could be escaped JSON)
                try:
                    mcp_data = json.loads(mcp_data)
                except json.JSONDecodeError:
                    # If we still have a string, create a simple dictionary with the data
                    mcp_data = {
                        "summary": mcp_data,
                        "raw_response": mcp_data
                    }
            
            # Generate formatted report based on selected format
            if output_format == "markdown":
                report = self._format_markdown(mcp_data)
            elif output_format == "html":
                report = self._format_html(mcp_data)
            else:
                report = self._format_text(mcp_data)
                
            return Message(text=report)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return Message(text=f"Error formatting report: {str(e)}\n\nTraceback: {tb}\n\nOriginal data:\n{input_text[:500]}...")
    
    def _format_markdown(self, data: Dict[str, Any]) -> str:
        """Format data as Markdown"""
        # Extra safety - ensure data is a dictionary
        if not isinstance(data, dict):
            # If we received a non-dict, create a simple report with the raw data
            return f"# MCP Analysis Report\n\n## Raw Response\n\n```\n{data}\n```"
            
        report_parts = []
        
        # Title
        report_parts.append("# Git Diff Analysis Report\n")
        
        # Repository info
        if "repository" in data:
            report_parts.append(f"**Repository**: [{data['repository']}]({data['repository']})\n")
        
        # Commit information
        if "base_commit" in data and "target_commit" in data:
            base = data["base_commit"] if isinstance(data["base_commit"], dict) else {"id": str(data["base_commit"])}
            target = data["target_commit"] if isinstance(data["target_commit"], dict) else {"id": str(data["target_commit"])}
            
            report_parts.append("## Commit Information\n")
            report_parts.append("### Base Commit\n")
            report_parts.append(f"- **ID**: `{base if isinstance(base, str) else base.get('id', 'N/A')}`")
            if isinstance(base, dict):
                report_parts.append(f"- **Message**: {base.get('message', 'N/A')}")
                report_parts.append(f"- **Author**: {base.get('author', 'N/A')}")
                report_parts.append(f"- **Date**: {base.get('date', 'N/A')}")
            report_parts.append("")
            
            report_parts.append("### Target Commit\n")
            report_parts.append(f"- **ID**: `{target if isinstance(target, str) else target.get('id', 'N/A')}`")
            if isinstance(target, dict):
                report_parts.append(f"- **Message**: {target.get('message', 'N/A')}")
                report_parts.append(f"- **Author**: {target.get('author', 'N/A')}")
                report_parts.append(f"- **Date**: {target.get('date', 'N/A')}")
            report_parts.append("")
        
        # Summary section
        if "summary" in data:
            report_parts.append("## Summary\n")
            report_parts.append(f"{data['summary']}\n")
        
        # Package Changes - Process specific MCP requirements analyzer format
        has_package_changes = False
        
        # Added packages
        if "added_packages" in data and data["added_packages"]:
            has_package_changes = True
            report_parts.append("## Added Dependencies ➕\n")
            added = data["added_packages"]
            
            if isinstance(added, dict):
                for pkg_name, version in added.items():
                    report_parts.append(f"- `{pkg_name}`: `{version}`")
            elif isinstance(added, list):
                for pkg in added:
                    if isinstance(pkg, dict):
                        name = pkg.get("name", pkg.get("package", "Unknown"))
                        version = pkg.get("version", "Unknown")
                        report_parts.append(f"- `{name}`: `{version}`")
                    else:
                        report_parts.append(f"- `{pkg}`")
            report_parts.append("")
        
        # Removed packages
        if "removed_packages" in data and data["removed_packages"]:
            has_package_changes = True
            report_parts.append("## Removed Dependencies ➖\n")
            removed = data["removed_packages"]
            
            if isinstance(removed, dict):
                for pkg_name, version in removed.items():
                    if version:  # If version is provided
                        report_parts.append(f"- `{pkg_name}`: `{version}`")
                    else:  # If just the package name
                        report_parts.append(f"- `{pkg_name}`")
            elif isinstance(removed, list):
                for pkg in removed:
                    if isinstance(pkg, dict):
                        name = pkg.get("name", pkg.get("package", "Unknown"))
                        version = pkg.get("version", "Unknown")
                        report_parts.append(f"- `{name}`: `{version}`")
                    else:
                        report_parts.append(f"- `{pkg}`")
            report_parts.append("")
        
        # Changed packages
        if "changed_packages" in data and data["changed_packages"]:
            has_package_changes = True
            report_parts.append("## Changed Dependencies 🔄\n")
            changed = data["changed_packages"]
            
            if isinstance(changed, dict):
                for pkg_name, versions in changed.items():
                    if isinstance(versions, dict):
                        old_ver = versions.get("old", "Unknown")
                        new_ver = versions.get("new", "Unknown")
                        report_parts.append(f"- `{pkg_name}`: `{old_ver}` → `{new_ver}`")
                    else:
                        report_parts.append(f"- `{pkg_name}`: `{versions}`")
            elif isinstance(changed, list):
                for pkg in changed:
                    if isinstance(pkg, dict):
                        name = pkg.get("name", pkg.get("package", "Unknown"))
                        old_ver = pkg.get("old_version", pkg.get("old", "Unknown"))
                        new_ver = pkg.get("new_version", pkg.get("new", "Unknown"))
                        report_parts.append(f"- `{name}`: `{old_ver}` → `{new_ver}`")
                    else:
                        report_parts.append(f"- `{pkg}`")
            report_parts.append("")
        
        # AI Analysis section with dependency details
        if "ai_analysis" in data and isinstance(data["ai_analysis"], dict):
            ai_analysis = data["ai_analysis"]
            
            # Risk Assessment section
            if "dependency_analysis" in ai_analysis and isinstance(ai_analysis["dependency_analysis"], dict):
                dep_analysis = ai_analysis["dependency_analysis"]
                
                # Detailed analysis of added dependencies
                if "added_dependencies" in dep_analysis and dep_analysis["added_dependencies"]:
                    report_parts.append("## Detailed Analysis: Added Dependencies\n")
                    for dep in dep_analysis["added_dependencies"]:
                        if isinstance(dep, dict):
                            pkg_name = dep.get("package", "Unknown")
                            version = dep.get("version", "Unknown")
                            risk = dep.get("risk_level", "unknown")
                            
                            # Emoji based on risk level
                            risk_emoji = "🔴" if risk == "high" else "🟠" if risk == "medium" else "🟡" if risk == "low" else "⚪"
                            
                            report_parts.append(f"### {pkg_name} {risk_emoji}\n")
                            report_parts.append(f"- **Version**: `{version}`")
                            report_parts.append(f"- **Risk Level**: {risk.upper()}")
                            
                            if "analysis" in dep:
                                report_parts.append(f"- **Analysis**: {dep['analysis']}")
                            
                            if "recommendations" in dep and dep["recommendations"]:
                                report_parts.append("- **Recommendations**:")
                                for rec in dep["recommendations"]:
                                    report_parts.append(f"  - {rec}")
                            
                            report_parts.append("")
                
                # Detailed analysis of changed dependencies
                if "changed_dependencies" in dep_analysis and dep_analysis["changed_dependencies"]:
                    report_parts.append("## Detailed Analysis: Changed Dependencies\n")
                    for dep in dep_analysis["changed_dependencies"]:
                        if isinstance(dep, dict):
                            pkg_name = dep.get("package", "Unknown")
                            old_ver = dep.get("old_version", "Unknown")
                            new_ver = dep.get("new_version", "Unknown")
                            risk = dep.get("risk_level", "unknown")
                            
                            # Emoji based on risk level
                            risk_emoji = "🔴" if risk == "high" else "🟠" if risk == "medium" else "🟡" if risk == "low" else "⚪"
                            
                            report_parts.append(f"### {pkg_name} {risk_emoji}\n")
                            report_parts.append(f"- **Version Change**: `{old_ver}` → `{new_ver}`")
                            report_parts.append(f"- **Risk Level**: {risk.upper()}")
                            
                            if "analysis" in dep:
                                report_parts.append(f"- **Analysis**: {dep['analysis']}")
                            
                            if "recommendations" in dep and dep["recommendations"]:
                                report_parts.append("- **Recommendations**:")
                                for rec in dep["recommendations"]:
                                    report_parts.append(f"  - {rec}")
                            
                            report_parts.append("")
                
                # Risk Assessment Overview
                if "risk_assessment" in dep_analysis and isinstance(dep_analysis["risk_assessment"], dict):
                    risk_assessment = dep_analysis["risk_assessment"]
                    report_parts.append("## Risk Assessment\n")
                    
                    # High risk packages
                    if "high_risk" in risk_assessment and risk_assessment["high_risk"]:
                        report_parts.append("### 🔴 High Risk\n")
                        for pkg in risk_assessment["high_risk"]:
                            if isinstance(pkg, dict):
                                name = pkg.get("package", "Unknown")
                                report_parts.append(f"- **{name}**")
                                if "analysis" in pkg:
                                    report_parts.append(f"  - {pkg['analysis']}")
                        report_parts.append("")
                    
                    # Medium risk packages
                    if "medium_risk" in risk_assessment and risk_assessment["medium_risk"]:
                        report_parts.append("### 🟠 Medium Risk\n")
                        for pkg in risk_assessment["medium_risk"]:
                            if isinstance(pkg, dict):
                                name = pkg.get("package", "Unknown")
                                report_parts.append(f"- **{name}**")
                                if "analysis" in pkg:
                                    report_parts.append(f"  - {pkg['analysis']}")
                        report_parts.append("")
                    
                    # Low risk packages
                    if "low_risk" in risk_assessment and risk_assessment["low_risk"]:
                        report_parts.append("### 🟡 Low Risk\n")
                        for pkg in risk_assessment["low_risk"]:
                            if isinstance(pkg, dict):
                                name = pkg.get("package", "Unknown")
                                report_parts.append(f"- **{name}**")
                                if "analysis" in pkg:
                                    report_parts.append(f"  - {pkg['analysis']}")
                        report_parts.append("")
                
                # Overall Recommendations
                if "recommendations" in dep_analysis and dep_analysis["recommendations"]:
                    report_parts.append("## Overall Recommendations\n")
                    for i, rec in enumerate(dep_analysis["recommendations"], 1):
                        report_parts.append(f"{i}. {rec}")
                    report_parts.append("")
        
        # General Recommendations section
        if "recommendations" in data and data["recommendations"]:
            report_parts.append("## General Recommendations\n")
            for i, rec in enumerate(data["recommendations"], 1):
                report_parts.append(f"{i}. {rec}")
            report_parts.append("")
        
        # Potential issues section
        if "potential_issues" in data and data["potential_issues"]:
            report_parts.append("## Potential Issues ⚠️\n")
            for issue in data["potential_issues"]:
                if isinstance(issue, dict):
                    title = issue.get("title", "Unknown issue")
                    severity = issue.get("severity", "medium")
                    
                    # Format severity with emoji
                    severity_emoji = "🔴" if severity == "high" else "🟠" if severity == "medium" else "🟡"
                    
                    report_parts.append(f"### {severity_emoji} {title}\n")
                    
                    if "description" in issue:
                        report_parts.append(issue["description"])
                    
                    if "solution" in issue:
                        report_parts.append(f"\n**Solution**: {issue['solution']}")
                    
                    report_parts.append("")
                else:
                    report_parts.append(f"- {issue}\n")
        
        # Issue counts if available
        if "issue_counts" in data and isinstance(data["issue_counts"], dict):
            counts = data["issue_counts"]
            report_parts.append("## Issue Summary\n")
            report_parts.append(f"- 🔴 **High**: {counts.get('high', 0)}")
            report_parts.append(f"- 🟠 **Medium**: {counts.get('medium', 0)}")
            report_parts.append(f"- 🟡 **Low**: {counts.get('low', 0)}")
            if "unknown" in counts:
                report_parts.append(f"- ⚪ **Unknown**: {counts.get('unknown', 0)}")
            report_parts.append("")
            
        # If we still don't have much content, include a raw data section
        if len(report_parts) <= 3 and not has_package_changes:  # Only title and maybe summary added
            report_parts.append("## Raw Data\n")
            report_parts.append("```json\n")
            report_parts.append(json.dumps(data, indent=2))
            report_parts.append("\n```\n")
            
        return "\n".join(report_parts)
    
    def _format_html(self, data: Dict[str, Any]) -> str:
        """Format data as HTML"""
        # Convert to markdown first then add HTML styling
        md_content = self._format_markdown(data)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Git Diff Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #3498db; margin-top: 20px; }}
                h3 {{ color: #2980b9; }}
                code, pre {{ background-color: #f7f7f7; padding: 2px 5px; border-radius: 3px; font-family: monospace; }}
                .container {{ max-width: 1000px; margin: 0 auto; }}
                .stats {{ display: flex; justify-content: space-around; text-align: center; margin: 20px 0; }}
                .stat-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .changes-list {{ list-style-type: none; padding-left: 10px; }}
                .changes-list li {{ margin-bottom: 5px; }}
                .changes-list li:before {{ content: "• "; color: #3498db; }}
                .addition {{ color: #27ae60; }}
                .deletion {{ color: #e74c3c; }}
                .warning {{ color: #e67e22; }}
                .compatible {{ color: #27ae60; }}
                .incompatible {{ color: #e74c3c; }}
            </style>
        </head>
        <body>
            <div class="container">
                <!-- Content will be replaced with real content -->
                <div id="content">
                    Replace this with the Markdown content
                </div>
            </div>
            
            <!-- Simple script to convert markdown to HTML -->
            <script>
                // This is just a placeholder - real conversion would need a proper markdown library
                // or server-side rendering
                document.getElementById('content').innerHTML = `{md_content.replace("`", "\\`")}`;
            </script>
        </body>
        </html>
        """
        
        return html
    
    def _format_text(self, data: Dict[str, Any]) -> str:
        """Format data as plain text"""
        # Simplify the markdown output by removing formatting characters
        text = self._format_markdown(data)
        text = text.replace("# ", "").replace("## ", "").replace("### ", "")
        text = text.replace("**", "").replace("*", "").replace("`", "")
        
        return text 