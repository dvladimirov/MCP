import os
import git
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
import subprocess
from mcp.requirements_analyzer import RequirementsAnalyzer

class GitRepository:
    """Class representing a Git repository"""
    
    def __init__(self, repo_url: str, local_path: Optional[str] = None):
        """Initialize a Git repository
        
        Args:
            repo_url: URL of the Git repository
            local_path: Local path to clone the repository to. If None, a temporary directory is used.
        """
        self.repo_url = repo_url
        self._temp_dir = None
        
        if local_path:
            self.local_path = local_path
            self._temp_dir = None
        else:
            self._temp_dir = tempfile.mkdtemp()
            self.local_path = self._temp_dir
    
    def clone(self) -> bool:
        """Clone the repository to the local path
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            git.Repo.clone_from(self.repo_url, self.local_path)
            return True
        except Exception as e:
            print(f"Error cloning repository: {e}")
            return False
    
    def get_file_list(self) -> List[str]:
        """Get a list of files in the repository
        
        Returns:
            List[str]: List of file paths
        """
        files = []
        for root, _, filenames in os.walk(self.local_path):
            for filename in filenames:
                # Skip .git directory files
                if '.git' in root:
                    continue
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, self.local_path)
                files.append(rel_path)
        return files
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get the content of a file
        
        Args:
            file_path: Path to the file relative to the repository root
            
        Returns:
            Optional[str]: File content as string, or None if the file doesn't exist
        """
        full_path = os.path.join(self.local_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def analyze_repo(self) -> Dict[str, Any]:
        """Analyze the repository and return information about it
        
        Returns:
            Dict[str, Any]: Repository information
        """
        try:
            repo = git.Repo(self.local_path)
            
            # Get basic repo info
            repo_info = {
                "url": self.repo_url,
                "active_branch": str(repo.active_branch),
                "last_commit": {
                    "id": repo.head.commit.hexsha,
                    "author": repo.head.commit.author.name,
                    "message": repo.head.commit.message.strip(),
                    "date": repo.head.commit.committed_datetime.isoformat(),
                },
                "file_count": len(self.get_file_list()),
                "directory_structure": self._get_directory_structure()
            }
            
            return repo_info
            
        except Exception as e:
            print(f"Error analyzing repository: {e}")
            return {"error": str(e)}
    
    def _get_directory_structure(self) -> Dict[str, Any]:
        """Get the directory structure of the repository
        
        Returns:
            Dict[str, Any]: Directory structure as a nested dictionary
        """
        structure = {}
        for file_path in self.get_file_list():
            path_parts = file_path.split(os.sep)
            current = structure
            
            # Build nested dict representing directory structure
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:  # Leaf/file
                    current[part] = None
                else:  # Directory
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        return structure
    
    def find_files_by_extension(self, extension: str) -> List[str]:
        """Find files with a specific extension
        
        Args:
            extension: File extension to search for (e.g., '.py')
            
        Returns:
            List[str]: List of file paths
        """
        return [f for f in self.get_file_list() if f.endswith(extension)]
    
    def find_files_by_content(self, pattern: str) -> List[str]:
        """Find files containing a specific pattern
        
        Args:
            pattern: Content pattern to search for
            
        Returns:
            List[str]: List of file paths
        """
        matching_files = []
        
        try:
            # Use grep for efficient searching
            cmd = f'grep -r "{pattern}" --include="*" {self.local_path} | cut -d: -f1'
            output = subprocess.check_output(cmd, shell=True, text=True)
            
            # Convert absolute paths to relative paths
            for line in output.splitlines():
                rel_path = os.path.relpath(line, self.local_path)
                matching_files.append(rel_path)
                
        except subprocess.CalledProcessError:
            # No matches found or error in grep
            pass
            
        return matching_files
    
    def cleanup(self):
        """Clean up temporary directory if used"""
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)
    
    def get_last_commit_diff(self) -> Dict[str, Any]:
        """Get the diff of the last commit
        
        Returns:
            Dict[str, Any]: Diff information of the last commit
        """
        try:
            repo = git.Repo(self.local_path)
            
            # Get the last commit
            last_commit = repo.head.commit
            
            # Get the parent commit (to compare with)
            parent_commit = last_commit.parents[0] if last_commit.parents else None
            
            if not parent_commit:
                return {
                    "error": "No parent commit found",
                    "commit_id": last_commit.hexsha,
                    "commit_message": last_commit.message.strip(),
                    "files_changed": [],
                    "total_additions": 0,
                    "total_deletions": 0
                }
            
            # Get the diff between the last commit and its parent
            diff_index = parent_commit.diff(last_commit)
            
            # Collect changed files and their stats
            files_changed = []
            total_additions = 0
            total_deletions = 0
            
            for diff_item in diff_index:
                try:
                    # Get the diff stats
                    file_path = diff_item.a_path if diff_item.a_path else diff_item.b_path
                    change_type = diff_item.change_type
                    
                    # Get the actual diff content
                    diff_content = ""
                    if hasattr(diff_item, 'diff'):
                        diff_content = diff_item.diff.decode('utf-8', errors='replace')
                    
                    # Count lines added/removed
                    additions = 0
                    deletions = 0
                    
                    for line in diff_content.split('\n'):
                        if line.startswith('+') and not line.startswith('+++'):
                            additions += 1
                        elif line.startswith('-') and not line.startswith('---'):
                            deletions += 1
                    
                    # Add to totals
                    total_additions += additions
                    total_deletions += deletions
                    
                    # Add file info to the list
                    files_changed.append({
                        "path": file_path,
                        "change_type": change_type,
                        "additions": additions,
                        "deletions": deletions,
                        "diff": diff_content if len(diff_content) < 5000 else diff_content[:5000] + "... [truncated]"
                    })
                    
                except Exception as e:
                    print(f"Error processing diff for file: {e}")
                    continue
            
            # Create the result object
            result = {
                "commit_id": last_commit.hexsha,
                "commit_message": last_commit.message.strip(),
                "commit_author": last_commit.author.name,
                "commit_date": last_commit.committed_datetime.isoformat(),
                "files_changed": files_changed,
                "total_files_changed": len(files_changed),
                "total_additions": total_additions,
                "total_deletions": total_deletions
            }
            
            return result
            
        except Exception as e:
            print(f"Error getting last commit diff: {e}")
            return {"error": str(e)}

    def get_commit_diff(self, base_commit_sha: str, target_commit_sha: str = 'HEAD') -> Dict[str, Any]:
        """Get the diff between two arbitrary commits
        
        Args:
            base_commit_sha: SHA of the base commit
            target_commit_sha: SHA of the target commit (default: HEAD)
            
        Returns:
            Dict[str, Any]: Diff information between the commits
        """
        try:
            repo = git.Repo(self.local_path)
            
            # Fetch the commits
            try:
                base_commit = repo.commit(base_commit_sha)
            except Exception as e:
                print(f"Error finding base commit: {e}")
                return {"error": f"Base commit not found: {base_commit_sha}"}
                
            try:
                target_commit = repo.commit(target_commit_sha) if target_commit_sha != 'HEAD' else repo.head.commit
            except Exception as e:
                print(f"Error finding target commit: {e}")
                return {"error": f"Target commit not found: {target_commit_sha}"}
            
            # Get the diff between the commits
            diff_index = base_commit.diff(target_commit)
            
            # Collect changed files and their stats
            files_changed = []
            total_additions = 0
            total_deletions = 0
            
            for diff_item in diff_index:
                try:
                    # Get the diff stats
                    file_path = diff_item.a_path if diff_item.a_path else diff_item.b_path
                    change_type = diff_item.change_type
                    
                    # Get the actual diff content
                    diff_content = ""
                    if hasattr(diff_item, 'diff'):
                        diff_content = diff_item.diff.decode('utf-8', errors='replace')
                    
                    # Count lines added/removed
                    additions = 0
                    deletions = 0
                    
                    for line in diff_content.split('\n'):
                        if line.startswith('+') and not line.startswith('+++'):
                            additions += 1
                        elif line.startswith('-') and not line.startswith('---'):
                            deletions += 1
                    
                    # Add to totals
                    total_additions += additions
                    total_deletions += deletions
                    
                    # Add file info to the list
                    files_changed.append({
                        "path": file_path,
                        "change_type": change_type,
                        "additions": additions,
                        "deletions": deletions,
                        "diff": diff_content if len(diff_content) < 5000 else diff_content[:5000] + "... [truncated]"
                    })
                    
                except Exception as e:
                    print(f"Error processing diff for file: {e}")
                    continue
            
            # Create the result object
            result = {
                "base_commit": {
                    "id": base_commit.hexsha,
                    "message": base_commit.message.strip(),
                    "author": base_commit.author.name,
                    "date": base_commit.committed_datetime.isoformat()
                },
                "target_commit": {
                    "id": target_commit.hexsha,
                    "message": target_commit.message.strip(),
                    "author": target_commit.author.name,
                    "date": target_commit.committed_datetime.isoformat()
                },
                "files_changed": files_changed,
                "total_files_changed": len(files_changed),
                "total_additions": total_additions,
                "total_deletions": total_deletions
            }
            
            return result
            
        except Exception as e:
            print(f"Error getting commit diff: {e}")
            return {"error": str(e)}

class GitService:
    """Service for handling Git operations"""
    
    @staticmethod
    def analyze_repository(repo_url: str) -> Dict[str, Any]:
        """Analyze a Git repository
        
        Args:
            repo_url: URL of the Git repository
            
        Returns:
            Dict[str, Any]: Repository analysis results
        """
        repo = GitRepository(repo_url)
        
        try:
            success = repo.clone()
            if not success:
                return {"error": "Failed to clone repository"}
            
            analysis = repo.analyze_repo()
            
            # Add file statistics by type
            py_files = repo.find_files_by_extension('.py')
            js_files = repo.find_files_by_extension('.js')
            html_files = repo.find_files_by_extension('.html')
            
            analysis["file_stats"] = {
                "python_files": len(py_files),
                "javascript_files": len(js_files),
                "html_files": len(html_files)
            }
            
            return analysis
            
        finally:
            repo.cleanup()
    
    @staticmethod
    def search_repository(repo_url: str, pattern: str) -> Dict[str, Any]:
        """Search a Git repository for files matching a pattern
        
        Args:
            repo_url: URL of the Git repository
            pattern: Content pattern to search for
            
        Returns:
            Dict[str, Any]: Search results
        """
        repo = GitRepository(repo_url)
        
        try:
            success = repo.clone()
            if not success:
                return {"error": "Failed to clone repository"}
            
            matching_files = repo.find_files_by_content(pattern)
            
            result = {
                "repo_url": repo_url,
                "pattern": pattern,
                "matching_files": matching_files,
                "match_count": len(matching_files)
            }
            
            return result
            
        finally:
            repo.cleanup()
    
    @staticmethod
    def get_last_commit_diff(repo_url: str) -> Dict[str, Any]:
        """Get the diff of the last commit in a repository
        
        Args:
            repo_url: URL of the Git repository
            
        Returns:
            Dict[str, Any]: Diff information
        """
        repo = GitRepository(repo_url)
        
        try:
            success = repo.clone()
            if not success:
                return {"error": "Failed to clone repository"}
            
            diff_info = repo.get_last_commit_diff()
            return diff_info
            
        finally:
            repo.cleanup()
            
    @staticmethod
    def get_commit_diff(repo_url: str, base_commit_sha: str, target_commit_sha: str = 'HEAD') -> Dict[str, Any]:
        """Get the diff between two commits in a repository
        
        Args:
            repo_url: URL of the Git repository
            base_commit_sha: SHA of the base commit
            target_commit_sha: SHA of the target commit (default: HEAD)
            
        Returns:
            Dict[str, Any]: Diff information between the commits
        """
        repo = GitRepository(repo_url)
        
        try:
            success = repo.clone()
            if not success:
                return {"error": "Failed to clone repository"}
            
            diff_info = repo.get_commit_diff(base_commit_sha, target_commit_sha)
            return diff_info
            
        finally:
            repo.cleanup()
    
    @staticmethod
    def analyze_requirements_changes(repo_url: str, base_commit_sha: str, target_commit_sha: str = 'HEAD') -> Dict[str, Any]:
        """Analyze changes in requirements.txt between two commits with detailed compatibility analysis
        
        Args:
            repo_url: URL of the Git repository
            base_commit_sha: SHA of the base commit
            target_commit_sha: SHA of the target commit (default: HEAD)
            
        Returns:
            Dict[str, Any]: Detailed analysis of requirements changes
        """
        repo = GitRepository(repo_url)
        
        try:
            success = repo.clone()
            if not success:
                return {"error": "Failed to clone repository"}
            
            # Get requirements.txt from both commits
            old_requirements = None
            new_requirements = None
            
            try:
                # First try the root requirements.txt
                old_requirements = GitService._get_file_from_commit(repo, base_commit_sha, "requirements.txt")
            except Exception:
                # Try looking for requirements files in other common locations
                for path in ["requirements/base.txt", "requirements/prod.txt", "requirements/production.txt"]:
                    try:
                        old_requirements = GitService._get_file_from_commit(repo, base_commit_sha, path)
                        if old_requirements:
                            break
                    except Exception:
                        continue
            
            try:
                # First try the root requirements.txt
                new_requirements = GitService._get_file_from_commit(repo, target_commit_sha, "requirements.txt")
            except Exception:
                # Try looking for requirements files in other common locations
                for path in ["requirements/base.txt", "requirements/prod.txt", "requirements/production.txt"]:
                    try:
                        new_requirements = GitService._get_file_from_commit(repo, target_commit_sha, path)
                        if new_requirements:
                            break
                    except Exception:
                        continue
            
            if not old_requirements and not new_requirements:
                return {
                    "status": "no_requirements",
                    "message": "No requirements.txt found in either commit",
                    "repository": repo_url,
                    "base_commit": base_commit_sha,
                    "target_commit": target_commit_sha
                }
            
            if not old_requirements:
                # Only new requirements exist - likely a new project
                return {
                    "status": "new_requirements",
                    "message": "requirements.txt was added in this diff",
                    "repository": repo_url,
                    "base_commit": base_commit_sha,
                    "target_commit": target_commit_sha,
                    "new_requirements": GitService._parse_requirements_to_dict(new_requirements)
                }
            
            if not new_requirements:
                # Only old requirements exist - requirements.txt was deleted
                return {
                    "status": "deleted_requirements",
                    "message": "requirements.txt was deleted in this diff",
                    "repository": repo_url,
                    "base_commit": base_commit_sha,
                    "target_commit": target_commit_sha,
                    "old_requirements": GitService._parse_requirements_to_dict(old_requirements)
                }
            
            # Use our dedicated RequirementsAnalyzer for enhanced analysis
            analyzer = RequirementsAnalyzer()
            analysis_results = analyzer.analyze_requirements_changes(old_requirements, new_requirements)
            
            # Create the summary
            issues_by_severity = analysis_results["issue_counts"]
            
            summary = f"Requirements diff analysis between {base_commit_sha[:7]} and {target_commit_sha[:7] if target_commit_sha != 'HEAD' else 'HEAD'} "
            summary += f"found {len(analysis_results['added_packages'])} added, {len(analysis_results['removed_packages'])} removed, and {len(analysis_results['changed_packages'])} changed dependencies. "
            
            if issues_by_severity["high"] > 0:
                summary += f"Detected {issues_by_severity['high']} high-severity issues that may cause breaking changes. "
            
            if issues_by_severity["medium"] > 0:
                summary += f"Found {issues_by_severity['medium']} medium-severity issues that deserve attention. "
            
            # Dynamic AI analysis of dependency changes
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
                # This is just a starting point - in a real implementation, this would be much more comprehensive
                if pkg_name.lower() == "django":
                    if version_spec.startswith("=="):
                        major_version = version_num.split('.')[0] if version_num != "unknown" else "unknown"
                        if major_version == "4":
                            analysis_text = f"Adding Django 4.x ({version_num}) which is a recent major version with potential breaking changes if upgrading from Django 3.x."
                            risk_level = "medium"
                            recommendations.append("If upgrading from Django 3.x, review the Django 4.0 release notes for breaking changes")
                
                elif pkg_name.lower() == "tensorflow":
                    analysis_text = f"Adding TensorFlow {version_spec} which is a complex machine learning framework with specific dependencies."
                    risk_level = "medium"
                    recommendations.append("Verify compatibility with GPU drivers if using GPU acceleration")
                    recommendations.append("Check dependency conflicts with other machine learning libraries")
                
                elif pkg_name.lower() == "flask":
                    analysis_text = f"Adding Flask {version_spec}, a lightweight web framework."
                    risk_level = "low"
                    if not any(dep.lower() in ["werkzeug", "jinja2", "itsdangerous", "click"] for dep in analysis_results["added_packages"]):
                        recommendations.append("Flask dependencies (Werkzeug, Jinja2, etc.) not explicitly included - Flask will install its own versions")
                
                # Store the analysis
                pkg_analysis = {
                    "package": pkg_name,
                    "version": version_spec,
                    "analysis": analysis_text or f"Added new dependency {pkg_name} {version_spec}.",
                    "risk_level": risk_level,
                    "recommendations": recommendations or ["Verify compatibility with existing codebase"]
                }
                
                ai_analysis["dependency_analysis"]["added_dependencies"].append(pkg_analysis)
            
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
                        
                        # Compare major versions
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
                            
                            elif new_parts[0] < old_parts[0]:
                                # Major version downgrade
                                risk_level = "high"
                                analysis_text = f"Major version downgrade from {old_ver} to {new_ver}. This may cause regression issues."
                                recommendations.append("Verify why the major version was downgraded")
                                recommendations.append("Run comprehensive tests to check for regression issues")
                    except (ValueError, IndexError):
                        # Couldn't parse version numbers
                        pass
                
                # Check for constraint changes
                if old_ver.startswith("==") and new_ver.startswith(">="):
                    risk_level = "medium"
                    analysis_text = f"Version constraint relaxed from exact {old_ver} to minimum {new_ver}."
                    recommendations.append(f"Relaxing version constraints can introduce compatibility issues as newer versions are installed")
                
                elif old_ver.startswith(">=") and new_ver.startswith("=="):
                    risk_level = "low"
                    analysis_text = f"Version constraint tightened from minimum {old_ver} to exact {new_ver}."
                    recommendations.append(f"Pinning to exact versions improves reproducibility")
                
                # Package-specific analysis based on common dependencies
                if pkg_name.lower() == "requests":
                    if new_ver.startswith("==2.2"):
                        recommendations.append("Requests 2.2x includes important security fixes")
                        risk_level = "low"
                
                elif pkg_name.lower() == "django":
                    if old_ver.startswith("==3") and new_ver.startswith("==4"):
                        risk_level = "high"
                        analysis_text = f"Major Django version upgrade from Django 3.x to Django 4.x. This includes breaking changes."
                        recommendations.append("Review Django 4.0 release notes for breaking changes")
                        recommendations.append("Run the Django upgrade checklist")
                
                elif pkg_name.lower() == "tensorflow":
                    risk_level = "high"
                    recommendations.append("TensorFlow updates often include significant API changes")
                    recommendations.append("Test machine learning models thoroughly with the new version")
                    recommendations.append("Check for deprecated API usage")
                
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
            
            # Return the complete analysis
            return {
                "status": "success",
                "repository": repo_url,
                "base_commit": base_commit_sha,
                "target_commit": target_commit_sha,
                "summary": summary.strip(),
                "added_packages": analysis_results["added_packages"],
                "removed_packages": analysis_results["removed_packages"],
                "changed_packages": analysis_results["changed_packages"],
                "potential_issues": analysis_results["potential_issues"],
                "recommendations": analysis_results["recommendations"],
                "issue_counts": issues_by_severity,
                "ai_analysis": ai_analysis
            }
            
        finally:
            repo.cleanup()
    
    @staticmethod
    def _get_file_from_commit(repo: GitRepository, commit_sha: str, file_path: str) -> Optional[str]:
        """Get the content of a file from a specific commit"""
        repo_obj = git.Repo(repo.local_path)
        
        try:
            # Get the file content at the specified commit
            file_content = repo_obj.git.show(f"{commit_sha}:{file_path}")
            return file_content
        except git.exc.GitCommandError:
            # File doesn't exist in that commit
            return None
    
    @staticmethod
    def _parse_requirements_to_dict(requirements_content: str) -> Dict[str, str]:
        """Parse requirements.txt content into a dictionary of package name -> version spec"""
        if not requirements_content or requirements_content.strip() == "":
            return {}
            
        result = {}
        for line in requirements_content.splitlines():
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                continue
                
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
            else:
                # Just package name or other format
                pkg_name = line.strip()
                result[pkg_name] = "any"
                
        return result 