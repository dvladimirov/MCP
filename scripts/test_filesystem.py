#!/usr/bin/env python3
import os
import sys

# Add the parent directory to Python path for proper imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import json
import tempfile
from pathlib import Path
from datetime import datetime
from langflow import MCPAIComponent
from typing import Dict, List, Any, Optional
import mimetypes

def analyze_filesystem(base_path: str = None, capture_output: bool = False) -> Dict[str, Any]:
    """
    Analyze the filesystem structure and provide statistics about file types, sizes, etc.
    
    Args:
        base_path (str): The base path to analyze. Defaults to the current directory.
        capture_output (bool): If True, return results without printing. If False, print results.
        
    Returns:
        Dict[str, Any]: A dictionary containing filesystem analysis data
    """
    if base_path is None:
        base_path = os.getcwd()
    
    # Initialize result data
    result = {
        "timestamp": datetime.now().isoformat(),
        "base_path": base_path,
        "files": [],
        "directories": [],
        "file_types": {},
        "total_size_bytes": 0,
        "largest_files": []
    }
    
    # Initialize mimetypes
    mimetypes.init()
    
    # Helper function to log information
    def log_info(message: str):
        if not capture_output:
            print(message)
    
    log_info(f"=== Analyzing Filesystem at {base_path} ===")
    
    # Walk the directory tree
    for root, dirs, files in os.walk(base_path):
        # Add directories to the result
        rel_root = os.path.relpath(root, base_path)
        if rel_root != ".":
            result["directories"].append(rel_root)
        
        # Process each file
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_path)
            
            try:
                # Get file stats
                file_stats = os.stat(file_path)
                size_bytes = file_stats.st_size
                result["total_size_bytes"] += size_bytes
                
                # Get file extension and mime type
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                if ext:
                    # Remove the dot from extension
                    ext = ext[1:]
                else:
                    ext = "no extension"
                
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = "application/octet-stream"
                
                # Update file type counts
                if ext in result["file_types"]:
                    result["file_types"][ext] += 1
                else:
                    result["file_types"][ext] = 1
                
                # Create file info
                file_info = {
                    "path": rel_path,
                    "size_bytes": size_bytes,
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "extension": ext,
                    "mime_type": mime_type
                }
                
                # Add to files list
                result["files"].append(file_info)
                
                # Check if it's one of the largest files
                if len(result["largest_files"]) < 10:
                    # Add the file to the list and sort by size
                    result["largest_files"].append(file_info)
                    result["largest_files"] = sorted(
                        result["largest_files"], 
                        key=lambda x: x["size_bytes"], 
                        reverse=True
                    )
                elif size_bytes > result["largest_files"][-1]["size_bytes"]:
                    # Replace the smallest file in the largest files list
                    result["largest_files"][-1] = file_info
                    result["largest_files"] = sorted(
                        result["largest_files"], 
                        key=lambda x: x["size_bytes"], 
                        reverse=True
                    )
                
            except (PermissionError, FileNotFoundError) as e:
                # Skip files we can't access
                if not capture_output:
                    print(f"Warning: Could not access {file_path}: {str(e)}")
                continue
    
    # Calculate additional statistics
    result["total_files"] = len(result["files"])
    result["total_directories"] = len(result["directories"])
    result["total_size_mb"] = result["total_size_bytes"] / (1024 * 1024)
    
    # Generate summary
    summary = (
        f"Found {result['total_files']} files in {result['total_directories']} directories\n"
        f"Total size: {result['total_size_mb']:.2f} MB\n"
        f"File types: {len(result['file_types'])} different extensions"
    )
    result["summary"] = summary
    
    # Try to get AI analysis of the filesystem
    try:
        mcp = MCPAIComponent(mcp_server_url="http://localhost:8000")
        models = mcp.list_models()
        
        # Check if we have a chat model available
        chat_models = [model for model in models if model.get('id', '').endswith('-chat')]
        
        if chat_models:
            log_info("Generating AI analysis of filesystem structure...")
            model_id = chat_models[0]['id']
            
            # Prepare file type summary for prompt
            file_types_summary = "\n".join([
                f"- {ext}: {count} files" 
                for ext, count in sorted(
                    result['file_types'].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10]
            ])
            
            # Prepare largest files summary
            largest_files_summary = "\n".join([
                f"- {file_info['path']}: {file_info['size_bytes'] / (1024 * 1024):.2f} MB" 
                for file_info in result['largest_files'][:5]
            ])
            
            # Create prompt
            prompt = f"""
            Analyze this filesystem structure and provide insights:
            
            Base path: {base_path}
            Total files: {result['total_files']}
            Total directories: {result['total_directories']}
            Total size: {result['total_size_mb']:.2f} MB
            
            Top file types:
            {file_types_summary}
            
            Largest files:
            {largest_files_summary}
            
            Please provide:
            1. A brief analysis of what type of project/codebase this appears to be
            2. Any anomalies or interesting patterns in the file structure
            3. Best practices or recommendations for organizing this filesystem
            
            Keep your response concise and focused on actionable insights.
            """
            
            # Get AI analysis
            response = mcp.chat(
                model_id=model_id,
                messages=[
                    {"role": "system", "content": "You are an expert filesystem analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                result["ai_analysis"] = response['choices'][0]['message']['content']
                log_info(f"AI Analysis generated successfully using model {model_id}")
            else:
                log_info("AI Analysis: No valid response received from the model.")
        else:
            log_info("AI Analysis: No chat models available.")
    except Exception as e:
        log_info(f"AI Analysis: Error - {str(e)}")
    
    # Print results if not capturing output
    if not capture_output:
        print(f"\n=== Filesystem Analysis Results ===")
        print(summary)
        
        print("\nTop 5 file types:")
        for i, (ext, count) in enumerate(
            sorted(result['file_types'].items(), key=lambda x: x[1], reverse=True)[:5]
        ):
            print(f"{i+1}. {ext}: {count} files")
        
        print("\nTop 5 largest files:")
        for i, file_info in enumerate(result['largest_files'][:5]):
            size_mb = file_info['size_bytes'] / (1024 * 1024)
            print(f"{i+1}. {file_info['path']} ({size_mb:.2f} MB)")
        
        if "ai_analysis" in result:
            print("\n=== AI Analysis ===")
            print(result["ai_analysis"])
    
    return result

def file_system_demo(capture_output=False):
    """
    Demonstrate filesystem operations with the option to capture results.
    
    Args:
        capture_output (bool): If True, return results instead of printing them
    
    Returns:
        list: List of operation results if capture_output is True, None otherwise
    """
    results = []
    
    def log_operation(operation, details):
        """Log an operation to results or print it"""
        result = {"operation": operation, "details": details, "timestamp": datetime.now().isoformat()}
        if capture_output:
            results.append(result)
        else:
            print(f"\n=== {operation} ===")
            for key, value in details.items():
                print(f"{key}: {value}")
    
    # Create a temporary directory for the demo
    temp_dir = tempfile.mkdtemp(prefix="mcp_fs_demo_")
    log_operation("Create Temporary Directory", {"path": temp_dir})
    
    # Create and write to a file
    test_file_path = os.path.join(temp_dir, "test_file.txt")
    with open(test_file_path, "w") as f:
        f.write("Hello from MCP filesystem test!\n")
        f.write("This file was created at: " + datetime.now().isoformat() + "\n")
    
    file_size = os.path.getsize(test_file_path)
    log_operation("Create File", {"path": test_file_path, "size_bytes": file_size})
    
    # Read the file
    with open(test_file_path, "r") as f:
        content = f.read()
    
    log_operation("Read File", {"path": test_file_path, "content": content, "length": len(content)})
    
    # Get file metadata
    file_stats = os.stat(test_file_path)
    metadata = {
        "size_bytes": file_stats.st_size,
        "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
        "accessed": datetime.fromtimestamp(file_stats.st_atime).isoformat(),
    }
    log_operation("File Metadata", {"path": test_file_path, "metadata": metadata})
    
    # Create a subdirectory
    subdir_path = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir_path, exist_ok=True)
    log_operation("Create Directory", {"path": subdir_path})
    
    # Create multiple files
    for i in range(3):
        file_path = os.path.join(subdir_path, f"file_{i}.txt")
        with open(file_path, "w") as f:
            f.write(f"This is file {i} in the subdirectory.\n")
        log_operation("Create Subdirectory File", {"path": file_path, "index": i})
    
    # List directory contents
    dir_contents = os.listdir(temp_dir)
    log_operation("List Directory", {"path": temp_dir, "contents": dir_contents})
    
    subdir_contents = os.listdir(subdir_path)
    log_operation("List Subdirectory", {"path": subdir_path, "contents": subdir_contents})
    
    # Recursive directory scan using Path
    all_files = list(Path(temp_dir).rglob("*"))
    all_files_str = [str(p.relative_to(temp_dir)) for p in all_files if p.is_file()]
    log_operation("Recursive Directory Scan", {"base_path": temp_dir, "files": all_files_str})
    
    # Update a file
    with open(test_file_path, "a") as f:
        f.write("\nThis line was appended to the file.\n")
    
    # Read updated file
    with open(test_file_path, "r") as f:
        updated_content = f.read()
    
    log_operation("Update File", {
        "path": test_file_path, 
        "updated_content": updated_content,
        "new_size_bytes": os.path.getsize(test_file_path)
    })
    
    # Rename a file
    renamed_path = os.path.join(temp_dir, "renamed_file.txt")
    os.rename(test_file_path, renamed_path)
    log_operation("Rename File", {"old_path": test_file_path, "new_path": renamed_path})
    
    # Delete files
    os.remove(renamed_path)
    log_operation("Delete File", {"path": renamed_path})
    
    for i in range(3):
        file_path = os.path.join(subdir_path, f"file_{i}.txt")
        os.remove(file_path)
        log_operation("Delete Subdirectory File", {"path": file_path})
    
    # Delete directories
    os.rmdir(subdir_path)
    log_operation("Delete Directory", {"path": subdir_path})
    
    os.rmdir(temp_dir)
    log_operation("Delete Temporary Directory", {"path": temp_dir})
    
    # If capturing output, return the results
    if capture_output:
        return results

def test_filesystem():
    """Test the filesystem functionality."""
    
    print("Initializing MCPAIComponent...")
    mcp = MCPAIComponent(mcp_server_url="http://localhost:8000")
    
    # Get current directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # List current directory contents
    print("\nContents of current directory:")
    contents = os.listdir(cwd)
    for item in contents[:10]:  # Show only first 10 items to avoid spam
        if os.path.isdir(os.path.join(cwd, item)):
            print(f" - 📁 {item}/")
        else:
            print(f" - 📄 {item}")
    
    if len(contents) > 10:
        print(f" ... and {len(contents) - 10} more items")
    
    # Run the filesystem demo with printing
    print("\nRunning filesystem operations demo...")
    file_system_demo(capture_output=False)
    
    print("\nFilesystem test completed successfully.")

if __name__ == "__main__":
    test_filesystem() 