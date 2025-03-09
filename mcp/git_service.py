import os
import git
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
import subprocess

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