import os
import glob
import shutil
import stat
import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

class FilesystemService:
    """Service for handling filesystem operations"""
    
    def __init__(self, allowed_directories: List[str] = None):
        """Initialize the filesystem service with allowed directories
        
        Args:
            allowed_directories: List of directories that are allowed to be accessed.
                                If None, the current directory is used.
        """
        if allowed_directories is None:
            # Default to current directory if no directories are specified
            self.allowed_directories = [os.getcwd()]
        else:
            # Convert all paths to absolute paths
            self.allowed_directories = [os.path.abspath(dir_path) for dir_path in allowed_directories]
    
    def _is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed to be accessed
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if path is allowed, False otherwise
        """
        abs_path = os.path.abspath(path)
        
        # Check if the path is within any of the allowed directories
        for allowed_dir in self.allowed_directories:
            if abs_path == allowed_dir or abs_path.startswith(allowed_dir + os.sep):
                return True
        
        return False
    
    def list_directory(self, path: str) -> List[Dict[str, str]]:
        """List contents of a directory
        
        Args:
            path: Directory path to list
            
        Returns:
            List[Dict[str, str]]: List of files and directories with their types
        """
        if not self._is_path_allowed(path):
            raise PermissionError(f"Access to path '{path}' is not allowed")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path '{path}' does not exist")
        
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Path '{path}' is not a directory")
        
        result = []
        with os.scandir(path) as entries:
            for entry in entries:
                entry_type = "FILE" if entry.is_file() else "DIR" if entry.is_dir() else "UNKNOWN"
                result.append({
                    "name": entry.name,
                    "type": entry_type,
                    "path": os.path.join(path, entry.name)
                })
        
        return result
    
    def read_file(self, path: str) -> str:
        """Read contents of a file
        
        Args:
            path: Path to the file
            
        Returns:
            str: Contents of the file
        """
        if not self._is_path_allowed(path):
            raise PermissionError(f"Access to path '{path}' is not allowed")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{path}' does not exist")
        
        if not os.path.isfile(path):
            raise IsADirectoryError(f"Path '{path}' is a directory, not a file")
        
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def read_multiple_files(self, paths: List[str]) -> Dict[str, Any]:
        """Read multiple files at once
        
        Args:
            paths: List of file paths
            
        Returns:
            Dict[str, Any]: Dictionary with file contents and error info
        """
        results = {}
        for path in paths:
            try:
                results[path] = {
                    "content": self.read_file(path),
                    "error": None
                }
            except Exception as e:
                results[path] = {
                    "content": None,
                    "error": str(e)
                }
        
        return results
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file
        
        Args:
            path: Path to the file
            content: Content to write
            
        Returns:
            Dict[str, Any]: Result information
        """
        if not self._is_path_allowed(path):
            raise PermissionError(f"Access to path '{path}' is not allowed")
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return {
            "path": path,
            "size": len(content),
            "success": True
        }
    
    def edit_file(self, path: str, edits: List[Dict[str, str]], dry_run: bool = False) -> Dict[str, Any]:
        """Edit a file with multiple replacements
        
        Args:
            path: Path to the file
            edits: List of edits to apply. Each edit has 'oldText' and 'newText'
            dry_run: Whether to simulate the edit without making changes
            
        Returns:
            Dict[str, Any]: Result of the operation including diff information
        """
        if not self._is_path_allowed(path):
            raise PermissionError(f"Access to path '{path}' is not allowed")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{path}' does not exist")
        
        # Read the original content
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Apply the edits
        new_content = content
        applied_edits = []
        failed_edits = []
        
        for edit in edits:
            old_text = edit.get('oldText', '')
            new_text = edit.get('newText', '')
            
            if old_text in new_content:
                new_content = new_content.replace(old_text, new_text)
                applied_edits.append({
                    "oldText": old_text,
                    "newText": new_text,
                    "success": True
                })
            else:
                failed_edits.append({
                    "oldText": old_text,
                    "newText": new_text,
                    "success": False,
                    "reason": "Text not found in file"
                })
        
        # Create a simple diff
        diff_lines = []
        for i, (old_line, new_line) in enumerate(zip(content.splitlines(), new_content.splitlines())):
            if old_line != new_line:
                diff_lines.append(f"Line {i+1}:")
                diff_lines.append(f"- {old_line}")
                diff_lines.append(f"+ {new_line}")
                diff_lines.append("")
        
        # If this is just a dry run, don't actually save the changes
        if not dry_run and applied_edits:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(new_content)
        
        return {
            "path": path,
            "originalSize": len(content),
            "newSize": len(new_content),
            "dryRun": dry_run,
            "appliedEdits": applied_edits,
            "failedEdits": failed_edits,
            "diff": "\n".join(diff_lines) if diff_lines else "No changes"
        }
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory
        
        Args:
            path: Path to the directory
            
        Returns:
            Dict[str, Any]: Result information
        """
        if not self._is_path_allowed(path):
            raise PermissionError(f"Access to path '{path}' is not allowed")
        
        # Create directory and parents if they don't exist
        os.makedirs(path, exist_ok=True)
        
        return {
            "path": path,
            "success": True
        }
    
    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move a file or directory
        
        Args:
            source: Source path
            destination: Destination path
            
        Returns:
            Dict[str, Any]: Result information
        """
        if not self._is_path_allowed(source) or not self._is_path_allowed(destination):
            raise PermissionError(f"Access to path '{source}' or '{destination}' is not allowed")
        
        if not os.path.exists(source):
            raise FileNotFoundError(f"Source '{source}' does not exist")
        
        if os.path.exists(destination):
            raise FileExistsError(f"Destination '{destination}' already exists")
        
        # Create destination directory if it doesn't exist
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        
        # Move the file or directory
        shutil.move(source, destination)
        
        return {
            "source": source,
            "destination": destination,
            "success": True
        }
    
    def search_files(self, path: str, pattern: str, exclude_patterns: List[str] = None) -> List[str]:
        """Search for files matching a pattern
        
        Args:
            path: Directory to search in
            pattern: Search pattern (glob format)
            exclude_patterns: Patterns to exclude
            
        Returns:
            List[str]: Matching file paths
        """
        if not self._is_path_allowed(path):
            raise PermissionError(f"Access to path '{path}' is not allowed")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path '{path}' does not exist")
        
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Path '{path}' is not a directory")
        
        # Normalize the path for glob
        path = os.path.normpath(path)
        
        # Get all files matching the pattern
        search_pattern = os.path.join(path, '**', pattern)
        matches = glob.glob(search_pattern, recursive=True)
        
        # Filter out excluded patterns
        if exclude_patterns:
            for exclude in exclude_patterns:
                exclude_matches = []
                for exclude_pattern in [os.path.join(path, '**', exclude)]:
                    exclude_matches.extend(glob.glob(exclude_pattern, recursive=True))
                matches = [m for m in matches if m not in exclude_matches]
        
        return matches
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get information about a file or directory
        
        Args:
            path: Path to the file or directory
            
        Returns:
            Dict[str, Any]: File information
        """
        if not self._is_path_allowed(path):
            raise PermissionError(f"Access to path '{path}' is not allowed")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path '{path}' does not exist")
        
        stat_info = os.stat(path)
        
        # Determine file type
        file_type = "UNKNOWN"
        if os.path.isfile(path):
            file_type = "FILE"
        elif os.path.isdir(path):
            file_type = "DIR"
        elif os.path.islink(path):
            file_type = "LINK"
        
        # Get file permissions in octal format
        mode = stat_info.st_mode
        permissions = stat.filemode(mode)
        
        # Format timestamps
        created = datetime.datetime.fromtimestamp(stat_info.st_ctime).isoformat()
        modified = datetime.datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        accessed = datetime.datetime.fromtimestamp(stat_info.st_atime).isoformat()
        
        return {
            "path": path,
            "name": os.path.basename(path),
            "size": stat_info.st_size,
            "type": file_type,
            "permissions": permissions,
            "created": created,
            "modified": modified,
            "accessed": accessed
        }
    
    def list_allowed_directories(self) -> List[str]:
        """List allowed directories
        
        Returns:
            List[str]: Allowed directories
        """
        return self.allowed_directories 