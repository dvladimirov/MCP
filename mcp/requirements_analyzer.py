import os
import re
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Set
import pkg_resources

class RequirementsAnalyzer:
    """Class for analyzing changes in requirements.txt files between git commits"""
    
    def __init__(self, compatibility_db_path: Optional[str] = None):
        """Initialize the requirements analyzer
        
        Args:
            compatibility_db_path: Optional path to a compatibility database JSON file
        """
        self.compatibility_db = {}
        if compatibility_db_path and os.path.exists(compatibility_db_path):
            import json
            try:
                with open(compatibility_db_path, 'r') as f:
                    self.compatibility_db = json.load(f)
            except Exception as e:
                print(f"Error loading compatibility database: {e}")
    
    def parse_requirements(self, requirements_content: str) -> Dict[str, str]:
        """Parse requirements.txt content into a dictionary of package name -> version spec
        
        Args:
            requirements_content: Content of requirements.txt
            
        Returns:
            Dict mapping package names to version specifications
        """
        if not requirements_content or requirements_content.strip() == "":
            return {}
            
        result = {}
        for line in requirements_content.splitlines():
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                continue
                
            # Remove any trailing comments
            if '#' in line:
                line = line.split('#')[0].strip()
            
            # Handle different formats: pkg==version, pkg>=version, etc.
            if '==' in line:
                # Standard version pinning (pkg==1.0.0)
                parts = line.split('==')
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = f"=={version}"
            elif '>=' in line:
                # Minimum version (pkg>=1.0.0)
                parts = line.split('>=')
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = f">={version}"
            elif '>' in line:
                # Greater than version (pkg>1.0.0)
                parts = line.split('>')
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = f">{version}"
            elif '<=' in line:
                # Maximum version (pkg<=1.0.0)
                parts = line.split('<=')
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = f"<={version}"
            elif '<' in line:
                # Less than version (pkg<1.0.0)
                parts = line.split('<')
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = f"<{version}"
            elif '~=' in line:
                # Compatible release (pkg~=1.0.0)
                parts = line.split('~=')
                pkg_name = parts[0].strip()
                version = parts[1].strip()
                result[pkg_name] = f"~={version}"
            elif re.search(r'[a-zA-Z0-9.\-_]+\[[a-zA-Z0-9.\-_,]+\]', line):
                # Handle packages with extras like requests[security]
                match = re.search(r'([a-zA-Z0-9.\-_]+)(\[[a-zA-Z0-9.\-_,]+\])', line)
                if match:
                    pkg_name = match.group(1)
                    extras = match.group(2)
                    result[f"{pkg_name}{extras}"] = "any"
            else:
                # Just package name or other format
                pkg_name = line.strip()
                result[pkg_name] = "any"
                
        return result
    
    def find_requirements_files(self, directory: str) -> List[str]:
        """Find requirements files in a directory
        
        Args:
            directory: Directory to search
            
        Returns:
            List of paths to requirements files
        """
        requirements_files = []
        
        # Common requirements file patterns
        patterns = [
            "requirements.txt",
            "requirements-*.txt",
            "requirements/*.txt",
            "requirements/base.txt",
            "requirements/prod.txt",
            "requirements/production.txt",
            "requirements/app.txt"
        ]
        
        for pattern in patterns:
            try:
                output = subprocess.check_output(
                    f"find {directory} -name '{pattern}' -not -path '*/\.*'",
                    shell=True,
                    text=True
                )
                files = [line.strip() for line in output.splitlines() if line.strip()]
                requirements_files.extend(files)
            except:
                pass
                
        return requirements_files
    
    def compare_requirements(
        self, 
        old_requirements: str, 
        new_requirements: str
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, Dict[str, str]]]:
        """Compare two requirements.txt files for changes
        
        Args:
            old_requirements: Content of the old requirements.txt
            new_requirements: Content of the new requirements.txt
            
        Returns:
            Tuple of (added_packages, removed_packages, changed_packages)
        """
        old_req_dict = self.parse_requirements(old_requirements)
        new_req_dict = self.parse_requirements(new_requirements)
        
        # Find added, removed, and changed packages
        added_packages = {}
        removed_packages = {}
        changed_packages = {}
        
        for pkg_name, version_spec in new_req_dict.items():
            if pkg_name not in old_req_dict:
                added_packages[pkg_name] = version_spec
            elif old_req_dict[pkg_name] != version_spec:
                changed_packages[pkg_name] = {
                    "old": old_req_dict[pkg_name],
                    "new": version_spec
                }
        
        for pkg_name, version_spec in old_req_dict.items():
            if pkg_name not in new_req_dict:
                removed_packages[pkg_name] = version_spec
        
        return added_packages, removed_packages, changed_packages
    
    def analyze_dependency_graph(self, requirements_dict: Dict[str, str]) -> Dict[str, Set[str]]:
        """Analyze the dependency graph for the given requirements
        
        Args:
            requirements_dict: Dict of package name -> version spec
            
        Returns:
            Dict mapping each package to its dependencies
        """
        dependency_graph = {}
        
        for pkg_name in requirements_dict:
            dependencies = set()
            
            # Try to get dependencies using pkg_resources
            try:
                # Normalize package name (remove version and extras)
                base_pkg_name = pkg_name.split('[')[0]
                
                # Check if package is installed
                try:
                    dist = pkg_resources.get_distribution(base_pkg_name)
                    for req in dist.requires():
                        dependencies.add(req.project_name)
                except:
                    # Package isn't installed, can't analyze dependencies
                    pass
            except:
                pass
                
            dependency_graph[pkg_name] = dependencies
            
        return dependency_graph
    
    def analyze_version_compatibility(
        self, 
        package_name: str, 
        old_version: str, 
        new_version: str
    ) -> Dict[str, Any]:
        """Analyze compatibility between two versions of a package
        
        Args:
            package_name: Name of the package
            old_version: Old version specification
            new_version: New version specification
            
        Returns:
            Dict with compatibility analysis
        """
        result = {
            "package": package_name,
            "old_version": old_version,
            "new_version": new_version,
            "potentially_breaking": False,
            "severity": "low",
            "description": "",
            "recommendations": []
        }
        
        # Helper to extract version numbers from version specs
        def extract_version(version_spec):
            if version_spec.startswith("=="):
                return version_spec[2:]
            elif version_spec.startswith(">="):
                return version_spec[2:]
            elif version_spec.startswith(">"):
                return version_spec[1:]
            elif version_spec.startswith("<="):
                return version_spec[2:]
            elif version_spec.startswith("<"):
                return version_spec[1:]
            elif version_spec.startswith("~="):
                return version_spec[2:]
            return None
        
        # Helper to parse version components
        def parse_version(version_str):
            if not version_str:
                return []
            
            # Handle dev/alpha/beta/rc versions
            version_parts = version_str.split('.')
            result = []
            
            for part in version_parts:
                # Extract numeric part
                match = re.search(r'^\d+', part)
                if match:
                    result.append(int(match.group(0)))
                else:
                    break
                    
            return result
        
        # Extract version numbers
        old_version_num = extract_version(old_version)
        new_version_num = extract_version(new_version)
        
        # If we couldn't extract versions, handle that case
        if not old_version_num or not new_version_num:
            if old_version != new_version:
                result["severity"] = "unknown"
                result["description"] = f"Version changed from {old_version} to {new_version}, but could not analyze compatibility"
                result["recommendations"].append(f"Review the changelog for {package_name} to identify potential issues")
            return result
        
        # Parse version components
        old_parts = parse_version(old_version_num)
        new_parts = parse_version(new_version_num)
        
        if not old_parts or not new_parts:
            # Couldn't parse version components
            result["severity"] = "unknown"
            result["description"] = f"Version changed from {old_version} to {new_version}, but could not parse version numbers"
            result["recommendations"].append(f"Review the changelog for {package_name} to identify potential issues")
            return result
        
        # Compare version components
        if len(old_parts) > 0 and len(new_parts) > 0:
            # Major version increase
            if new_parts[0] > old_parts[0]:
                result["potentially_breaking"] = True
                result["severity"] = "high"
                result["description"] = f"Major version upgrade from {old_version} to {new_version} might introduce breaking changes"
                result["recommendations"].append(f"Review {package_name} changelog for breaking changes between {old_version} and {new_version}")
                result["recommendations"].append(f"Run test suite to verify compatibility with {new_version}")
            # Minor version increase
            elif len(old_parts) > 1 and len(new_parts) > 1 and new_parts[1] > old_parts[1]:
                result["description"] = f"Minor version upgrade from {old_version} to {new_version} might add new features"
                result["recommendations"].append(f"Review {package_name} changelog for new features between {old_version} and {new_version}")
            # Patch version increase
            elif len(old_parts) > 2 and len(new_parts) > 2 and new_parts[2] > old_parts[2]:
                result["description"] = f"Patch version upgrade from {old_version} to {new_version} should be compatible"
                result["recommendations"].append(f"Check for bug fixes in {package_name} changelog")
            # Version downgrade
            elif new_parts[0] < old_parts[0] or (len(old_parts) > 1 and len(new_parts) > 1 and new_parts[1] < old_parts[1]):
                result["potentially_breaking"] = True
                result["severity"] = "medium"
                result["description"] = f"Version downgrade from {old_version} to {new_version} might cause regression issues"
                result["recommendations"].append(f"Verify why the version was downgraded")
                result["recommendations"].append(f"Run test suite to check for regression issues")
                
        # Check for constraint relaxation/tightening
        if old_version.startswith("==") and (new_version.startswith(">=") or new_version.startswith(">")):
            result["severity"] = "medium"
            result["description"] = f"Version constraint relaxed from exact {old_version} to minimum {new_version}, may allow newer versions with breaking changes"
            result["recommendations"].append(f"Consider pinning {package_name} to exact version if stability is important")
        elif (old_version.startswith(">=") or old_version.startswith(">")) and new_version.startswith("=="):
            result["severity"] = "low"
            result["description"] = f"Version constraint tightened from minimum {old_version} to exact {new_version}, improves reproducibility"
        
        # Check compatibility database if available
        if package_name in self.compatibility_db:
            for issue in self.compatibility_db[package_name]:
                if (issue["from_version"] == old_version_num and 
                    issue["to_version"] == new_version_num):
                    result["severity"] = issue["severity"]
                    result["description"] = issue["description"]
                    result["recommendations"] = issue["recommendations"]
                    result["potentially_breaking"] = issue["severity"] in ["high", "medium"]
                    break
                    
        return result
    
    def analyze_requirements_changes(
        self, 
        old_requirements: str, 
        new_requirements: str
    ) -> Dict[str, Any]:
        """Comprehensive analysis of changes between two requirements.txt files
        
        Args:
            old_requirements: Content of the old requirements.txt
            new_requirements: Content of the new requirements.txt
            
        Returns:
            Dict with detailed analysis results
        """
        # Compare requirements
        added_packages, removed_packages, changed_packages = self.compare_requirements(
            old_requirements, new_requirements
        )
        
        # Analyze potential issues and generate recommendations
        potential_issues = []
        recommendations = []
        
        # Check for potentially breaking changes in dependencies
        for pkg_name, change in changed_packages.items():
            old_ver = change["old"]
            new_ver = change["new"]
            
            # Analyze compatibility
            compatibility = self.analyze_version_compatibility(pkg_name, old_ver, new_ver)
            
            if compatibility["severity"] != "low":
                potential_issues.append({
                    "package": pkg_name,
                    "severity": compatibility["severity"],
                    "description": compatibility["description"]
                })
                
                for recommendation in compatibility["recommendations"]:
                    recommendations.append({
                        "package": pkg_name,
                        "recommendation": recommendation,
                        "action": "review_changelog" if "changelog" in recommendation else "test_compatibility"
                    })
        
        # Check for risky patterns in added dependencies
        for pkg_name, version_spec in added_packages.items():
            if version_spec == "any" or version_spec.startswith(">"):
                potential_issues.append({
                    "package": pkg_name,
                    "severity": "medium", 
                    "description": f"New dependency {pkg_name} with loose version constraint {version_spec} may lead to unexpected behavior"
                })
                recommendations.append({
                    "package": pkg_name,
                    "recommendation": f"Pin {pkg_name} to specific version for reproducibility",
                    "action": "pin_version"
                })
        
        # Analyze removed packages for potential impact
        if removed_packages:
            for pkg_name, version_spec in removed_packages.items():
                potential_issues.append({
                    "package": pkg_name,
                    "severity": "medium",
                    "description": f"Removal of dependency {pkg_name} {version_spec} may impact functionality if not properly replaced"
                })
                
                # Check if it might have been replaced by another package
                similar_packages = [new_pkg for new_pkg in added_packages.keys() 
                                    if pkg_name.lower() in new_pkg.lower() or 
                                    any(pkg_name.lower() in new_pkg.lower() for pkg_name in added_packages.keys())]
                
                if similar_packages:
                    recommendations.append({
                        "package": pkg_name,
                        "recommendation": f"Verify if {pkg_name} was replaced by {', '.join(similar_packages)}",
                        "action": "verify_replacement",
                        "related_packages": similar_packages
                    })
                else:
                    recommendations.append({
                        "package": pkg_name,
                        "recommendation": f"Ensure functionality previously provided by {pkg_name} is properly handled",
                        "action": "verify_functionality"
                    })
        
        # Analyze common dependency conflicts
        old_req_dict = self.parse_requirements(old_requirements)
        new_req_dict = self.parse_requirements(new_requirements)
        
        # Check for transitive dependency conflicts by analyzing dependencies
        old_deps_graph = self.analyze_dependency_graph(old_req_dict)
        new_deps_graph = self.analyze_dependency_graph(new_req_dict)
        
        # Look for potential conflicts where deps of newly added/changed packages
        # might conflict with existing dependencies
        for pkg_name, deps in new_deps_graph.items():
            for dep in deps:
                if dep in new_req_dict and dep in old_req_dict and new_req_dict[dep] != old_req_dict[dep]:
                    # This package's dependency has changed version
                    potential_issues.append({
                        "package": pkg_name,
                        "severity": "medium",
                        "description": f"Dependency {dep} of {pkg_name} has changed version, potential for conflicts"
                    })
                    recommendations.append({
                        "package": pkg_name,
                        "recommendation": f"Verify compatibility between {pkg_name} and {dep} {new_req_dict[dep]}",
                        "action": "verify_compatibility"
                    })
        
        # Create the summary
        issues_by_severity = {
            "high": len([i for i in potential_issues if i["severity"] == "high"]),
            "medium": len([i for i in potential_issues if i["severity"] == "medium"]),
            "low": len([i for i in potential_issues if i["severity"] == "low"]),
            "unknown": len([i for i in potential_issues if i["severity"] == "unknown"])
        }
        
        # Generate final analysis results
        result = {
            "added_packages": added_packages,
            "removed_packages": removed_packages,
            "changed_packages": changed_packages,
            "potential_issues": potential_issues,
            "recommendations": recommendations,
            "issue_counts": issues_by_severity
        }
        
        return result

# Example usage
if __name__ == "__main__":
    # Example requirements files
    old_requirements = """
    fastapi==0.70.0
    uvicorn==0.15.0
    openai==0.27.0
    requests==2.26.0
    pydantic==1.8.2
    """
    
    new_requirements = """
    fastapi==0.103.1
    uvicorn==0.23.2
    openai>=1.3.0
    requests==2.31.0
    pydantic>=2.4.2
    gitpython==3.1.40
    """
    
    analyzer = RequirementsAnalyzer()
    results = analyzer.analyze_requirements_changes(old_requirements, new_requirements)
    
    # Show results
    print(f"Added packages: {results['added_packages']}")
    print(f"Removed packages: {results['removed_packages']}")
    print(f"Changed packages: {results['changed_packages']}")
    print(f"Potential issues: {results['potential_issues']}")
    print(f"Recommendations: {results['recommendations']}") 