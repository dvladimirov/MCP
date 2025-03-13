#!/usr/bin/env python3
import os
import sys
import json
import argparse
from typing import Dict, Any, List

# Add parent directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from mcp.requirements_analyzer import RequirementsAnalyzer

def analyze_requirements_diff(old_requirements: str, new_requirements: str) -> Dict[str, Any]:
    """Analyze the differences between two requirements.txt files
    
    Args:
        old_requirements: Content of old requirements.txt
        new_requirements: Content of new requirements.txt
        
    Returns:
        Dict containing analysis results
    """
    analyzer = RequirementsAnalyzer()
    return analyzer.analyze_requirements_changes(old_requirements, new_requirements)

def dynamic_ai_analysis(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate dynamic AI analysis of requirements changes
    
    Args:
        analysis_results: Analysis results from RequirementsAnalyzer
        
    Returns:
        Dict with AI-powered analysis
    """
    # Structure for AI analysis
    ai_analysis = {
        "dependency_analysis": {
            "added_dependencies": [],
            "changed_dependencies": [],
            "removed_dependencies": [],
            "risk_assessment": {
                "high_risk": [],
                "medium_risk": [],
                "low_risk": []
            },
            "recommendations": []
        }
    }
    
    # Dynamically analyze added dependencies
    for pkg_name, version_spec in analysis_results["added_packages"].items():
        # Extract version number if available
        version_num = version_spec[2:] if version_spec.startswith("==") else "unknown"
        
        # Base risk assessment
        risk_level = "medium"  # Default risk level
        analysis_text = ""
        recommendations = []
        
        # Assess common dependencies and patterns
        if pkg_name.lower() in ["pytest", "coverage", "flake8", "mypy", "black", "isort"]:
            # Development/testing dependencies are lower risk
            risk_level = "low"
            analysis_text = f"Adding the development dependency {pkg_name} {version_spec} is generally safe."
            recommendations.append(f"Consider adding {pkg_name} to dev-requirements.txt instead of main requirements if this is a development dependency")
        
        elif "security" in pkg_name.lower() or pkg_name.lower() in ["cryptography", "pyjwt", "bcrypt", "passlib"]:
            # Security-related packages deserve special attention
            risk_level = "medium"
            analysis_text = f"Adding the security-related package {pkg_name} {version_spec} should be reviewed carefully."
            recommendations.append(f"Review security implications of adding {pkg_name}")
            recommendations.append("Consider conducting a security review of this dependency")
        
        elif not version_spec.startswith("=="):
            # Unpinned versions are higher risk
            risk_level = "medium"
            analysis_text = f"Adding {pkg_name} with an unpinned version {version_spec} can lead to unexpected behavior in the future."
            recommendations.append(f"Consider pinning {pkg_name} to a specific version for better reproducibility")
        
        # Package-specific analysis based on common dependencies
        if pkg_name.lower() == "setuptools":
            analysis_text = f"Adding setuptools {version_spec}. This is a core Python packaging tool."
            risk_level = "low"
            recommendations.append("This is a standard development dependency")
        
        # Store the analysis
        pkg_analysis = {
            "package": pkg_name,
            "version": version_spec,
            "analysis": analysis_text or f"Added new dependency {pkg_name} {version_spec}.",
            "risk_level": risk_level,
            "recommendations": recommendations or ["Verify compatibility with existing codebase"]
        }
        
        ai_analysis["dependency_analysis"]["added_dependencies"].append(pkg_analysis)
    
    # Analyze changed dependencies
    for pkg_name, change in analysis_results["changed_packages"].items():
        old_ver = change["old"]
        new_ver = change["new"]
        
        # Extract version numbers if available
        old_ver_num = old_ver[2:] if old_ver.startswith("==") else "unknown"
        new_ver_num = new_ver[2:] if new_ver.startswith("==") else "unknown"
        
        # Default values
        risk_level = "medium"
        analysis_text = f"Changed {pkg_name} from {old_ver} to {new_ver}."
        recommendations = []
        
        # Basic version comparison for pinned versions
        if old_ver.startswith("==") and new_ver.startswith("=="):
            try:
                old_parts = [int(x) for x in old_ver_num.split('.')]
                new_parts = [int(x) for x in new_ver_num.split('.')]
                
                # Compare major versions (first component)
                if len(old_parts) > 0 and len(new_parts) > 0:
                    if new_parts[0] > old_parts[0]:
                        # Major version upgrade
                        risk_level = "high"
                        analysis_text = f"Major version upgrade from {old_ver} to {new_ver}. This may introduce breaking changes."
                        recommendations.append(f"Review {pkg_name} changelog for breaking changes between versions")
                        recommendations.append("Run comprehensive tests to verify compatibility")
                    
                    elif len(old_parts) > 1 and len(new_parts) > 1 and new_parts[1] > old_parts[1]:
                        # Minor version upgrade
                        risk_level = "medium"
                        analysis_text = f"Minor version upgrade from {old_ver} to {new_ver}. This may add new features."
                        recommendations.append(f"Review {pkg_name} changelog for new features")
                        recommendations.append("Test with the new version")
                    
                    elif len(old_parts) > 2 and len(new_parts) > 2 and new_parts[2] > old_parts[2]:
                        # Patch version upgrade
                        risk_level = "low"
                        analysis_text = f"Patch version upgrade from {old_ver} to {new_ver}. This likely includes bug fixes."
                        recommendations.append(f"Review {pkg_name} changelog for bug fixes")
            except (ValueError, IndexError):
                # Couldn't parse version numbers
                pass
        
        # Package-specific analysis
        if pkg_name.lower() == "tensorflow":
            analysis_text = "TensorFlow version changes often include API changes that may break existing code."
            risk_level = "high"
            recommendations.append("Test machine learning models thoroughly with the new version")
            recommendations.append("Check for deprecated API usage")
        
        elif pkg_name.lower() == "requests":
            if "2.27" in old_ver and "2.28" in new_ver:
                analysis_text = "Minor version upgrade in requests library. This is likely a safe change with security improvements."
                risk_level = "low"
                recommendations.append("This is a recommended security update")
        
        # Store the analysis
        pkg_analysis = {
            "package": pkg_name,
            "old_version": old_ver,
            "new_version": new_ver,
            "analysis": analysis_text,
            "risk_level": risk_level,
            "recommendations": recommendations or ["Test with the new version to ensure compatibility"]
        }
        
        ai_analysis["dependency_analysis"]["changed_dependencies"].append(pkg_analysis)
    
    # Analyze removed dependencies
    for pkg_name, version_spec in analysis_results["removed_packages"].items():
        # Base risk assessment
        risk_level = "medium"  # Default risk level for removals
        analysis_text = f"Removed dependency {pkg_name} {version_spec}."
        recommendations = []
        
        # Check for potential replacements in added packages
        potential_replacements = [
            added_pkg for added_pkg in analysis_results["added_packages"].keys()
            if added_pkg.lower().replace('-', '').replace('_', '') in pkg_name.lower().replace('-', '').replace('_', '') or
            pkg_name.lower().replace('-', '').replace('_', '') in added_pkg.lower().replace('-', '').replace('_', '')
        ]
        
        if potential_replacements:
            analysis_text += f" Possibly replaced by: {', '.join(potential_replacements)}."
            recommendations.append(f"Verify that {', '.join(potential_replacements)} provides equivalent functionality to {pkg_name}")
        else:
            analysis_text += " No obvious replacement was added."
            recommendations.append(f"Verify that {pkg_name} functionality is no longer needed or has been reimplemented")
            risk_level = "medium"  # Higher risk when removing with no replacement
        
        # Store the analysis
        pkg_analysis = {
            "package": pkg_name,
            "version": version_spec,
            "analysis": analysis_text,
            "risk_level": risk_level,
            "recommendations": recommendations
        }
        
        ai_analysis["dependency_analysis"]["removed_dependencies"].append(pkg_analysis)
    
    # Categorize all changes by risk level
    for section in ["added_dependencies", "changed_dependencies", "removed_dependencies"]:
        for pkg in ai_analysis["dependency_analysis"][section]:
            ai_analysis["dependency_analysis"]["risk_assessment"][f"{pkg['risk_level']}_risk"].append(pkg)
    
    # Generate overall recommendations based on actual risk assessment
    if ai_analysis["dependency_analysis"]["risk_assessment"]["high_risk"]:
        ai_analysis["dependency_analysis"]["recommendations"].append(
            f"High-risk changes detected ({len(ai_analysis['dependency_analysis']['risk_assessment']['high_risk'])} packages). " +
            "Please review the following packages carefully: " +
            ", ".join(pkg["package"] for pkg in ai_analysis["dependency_analysis"]["risk_assessment"]["high_risk"])
        )
    
    if ai_analysis["dependency_analysis"]["risk_assessment"]["medium_risk"]:
        ai_analysis["dependency_analysis"]["recommendations"].append(
            f"Medium-risk changes detected ({len(ai_analysis['dependency_analysis']['risk_assessment']['medium_risk'])} packages). " +
            "Review the following packages: " +
            ", ".join(pkg["package"] for pkg in ai_analysis["dependency_analysis"]["risk_assessment"]["medium_risk"])
        )
    
    if ai_analysis["dependency_analysis"]["risk_assessment"]["low_risk"]:
        ai_analysis["dependency_analysis"]["recommendations"].append(
            f"Low-risk changes detected ({len(ai_analysis['dependency_analysis']['risk_assessment']['low_risk'])} packages). " +
            "These changes are likely safe but should still be tested."
        )
    
    # Overall project recommendations
    if len(analysis_results["changed_packages"]) > 3:
        ai_analysis["dependency_analysis"]["recommendations"].append(
            f"This update changes {len(analysis_results['changed_packages'])} dependencies. " +
            "Consider implementing a staged rollout to identify any potential issues early."
        )
    
    # Dependency chain analysis
    critical_deps = [pkg for pkg in analysis_results["changed_packages"].keys() 
                 if pkg.lower() in ["django", "flask", "fastapi", "tensorflow", "pytorch", "numpy", "pandas"]]
    if critical_deps:
        ai_analysis["dependency_analysis"]["recommendations"].append(
            f"Changes to core dependencies ({', '.join(critical_deps)}) may affect many parts of your application. " +
            "Run comprehensive tests across all functionality."
        )
    
    return ai_analysis

def read_file_content(file_path: str) -> str:
    """Read content from a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        String content of the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def analyze_example():
    """Run an example analysis with predefined requirements"""
    old_requirements = """
    requests==2.27.1
    numpy==1.22.0
    matplotlib==3.5.1
    scikit-learn==1.0.0
    scipy==1.8.0
    tensorflow==2.8.0
    """
    
    new_requirements = """
    requests==2.28.1
    numpy==1.23.0
    matplotlib==3.6.0
    scikit-learn==1.1.2
    scipy==1.9.1
    tensorflow==2.10.0
    setuptools==59.8.0
    """
    
    print("Example Requirements Analysis")
    print("============================")
    print("\nOld requirements:")
    print(old_requirements)
    print("\nNew requirements:")
    print(new_requirements)
    
    # Run the analysis
    analysis = analyze_requirements_diff(old_requirements, new_requirements)
    
    # Add dynamic AI analysis
    ai_analysis = dynamic_ai_analysis(analysis)
    
    # Print the results
    print_analysis_results(analysis, ai_analysis)

def print_analysis_results(analysis: Dict[str, Any], ai_analysis: Dict[str, Any]):
    """Print formatted analysis results
    
    Args:
        analysis: Basic analysis results
        ai_analysis: AI-powered analysis results
    """
    # Print summary
    print("\nSummary of Changes:")
    print(f"Added: {len(analysis['added_packages'])} packages")
    print(f"Removed: {len(analysis['removed_packages'])} packages")
    print(f"Changed: {len(analysis['changed_packages'])} packages")
    
    # Print details
    if analysis['added_packages']:
        print("\nAdded Dependencies:")
        for pkg_name, version in analysis['added_packages'].items():
            print(f"  + {pkg_name}{version}")
    
    if analysis['removed_packages']:
        print("\nRemoved Dependencies:")
        for pkg_name, version in analysis['removed_packages'].items():
            print(f"  - {pkg_name}{version}")
    
    if analysis['changed_packages']:
        print("\nChanged Dependencies:")
        for pkg_name, change in analysis['changed_packages'].items():
            print(f"  ~ {pkg_name}: {change['old']} -> {change['new']}")
    
    # Print AI Analysis
    print("\nAI-Powered Dependency Analysis:")
    
    # Print risk assessment
    print("\nRisk Assessment:")
    risk_levels = {
        "high_risk": "High Risk",
        "medium_risk": "Medium Risk",
        "low_risk": "Low Risk"
    }
    
    for risk_level, heading in risk_levels.items():
        packages = ai_analysis["dependency_analysis"]["risk_assessment"][risk_level]
        if packages:
            print(f"\n{heading}:")
            for pkg in packages:
                print(f"  • {pkg['package']}: {pkg['analysis']}")
                for rec in pkg['recommendations']:
                    print(f"    - {rec}")
    
    # Print overall recommendations
    if ai_analysis["dependency_analysis"]["recommendations"]:
        print("\nOverall Recommendations:")
        for rec in ai_analysis["dependency_analysis"]["recommendations"]:
            print(f"  • {rec}")

def main():
    """Main function to handle command-line arguments"""
    parser = argparse.ArgumentParser(description="Analyze changes between two requirements.txt files")
    parser.add_argument("--old", help="Path to old requirements.txt file or content string")
    parser.add_argument("--new", help="Path to new requirements.txt file or content string")
    parser.add_argument("--example", action="store_true", help="Run with example requirements")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    if args.example:
        analyze_example()
        return
    
    if not args.old or not args.new:
        print("Error: Both --old and --new arguments are required unless using --example")
        parser.print_help()
        return
    
    # Check if inputs are file paths or direct content
    old_requirements = args.old
    new_requirements = args.new
    
    if os.path.isfile(args.old):
        old_requirements = read_file_content(args.old)
    
    if os.path.isfile(args.new):
        new_requirements = read_file_content(args.new)
    
    # Run the analysis
    analysis = analyze_requirements_diff(old_requirements, new_requirements)
    ai_analysis = dynamic_ai_analysis(analysis)
    
    if args.json:
        # Output as JSON
        result = {
            "basic_analysis": analysis,
            "ai_analysis": ai_analysis
        }
        print(json.dumps(result, indent=2))
    else:
        # Print formatted results
        print_analysis_results(analysis, ai_analysis)

if __name__ == "__main__":
    main() 