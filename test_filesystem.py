#!/usr/bin/env python3
import os
import sys
import json
from langflow import MCPAIComponent

def test_filesystem():
    """Test the filesystem functionality."""
    
    print("Initializing MCPAIComponent...")
    mcp = MCPAIComponent(mcp_server_url="http://localhost:8000")
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    try:
        # List contents of current directory
        print("\nListing contents of current directory...")
        dir_contents = mcp.list_directory()
        
        entries = dir_contents.get('entries', [])
        print(f"Found {len(entries)} entries:")
        
        files = []
        dirs = []
        
        for entry in entries:
            if entry.get('type') == 'FILE':
                files.append(entry.get('name'))
            elif entry.get('type') == 'DIR':
                dirs.append(entry.get('name'))
        
        print("\nDirectories:")
        for d in sorted(dirs):
            print(f"  - {d}/")
        
        print("\nFiles:")
        for f in sorted(files):
            print(f"  - {f}")
        
        # Get info for this script file
        this_file = os.path.basename(__file__)
        if this_file in files:
            print(f"\nGetting info for {this_file}...")
            file_info = mcp.get_file_info(this_file)
            
            print(f"Path: {file_info.get('path')}")
            print(f"Size: {file_info.get('size')} bytes")
            print(f"Type: {file_info.get('type')}")
            print(f"Permissions: {file_info.get('permissions')}")
            print(f"Last modified: {file_info.get('modified')}")
            
            # Read this script's content
            print(f"\nReading content of {this_file}...")
            file_content = mcp.read_file(this_file)
            content = file_content.get('content', '')
            print(f"File has {len(content)} characters and {len(content.splitlines())} lines")
            
            # Create a test directory
            test_dir = "test_filesystem_dir"
            if test_dir not in dirs:
                print(f"\nCreating test directory '{test_dir}'...")
                result = mcp.create_directory(test_dir)
                print(f"Result: {result.get('success', False)}")
            
            # Write a test file
            test_file = os.path.join(test_dir, "test_file.txt")
            print(f"\nWriting to test file '{test_file}'...")
            content_to_write = "This is a test file.\nCreated by the MCP filesystem test script.\n"
            write_result = mcp.write_file(test_file, content_to_write)
            print(f"Write success: {write_result.get('success', False)}")
            print(f"Size: {write_result.get('size', 0)} bytes")
            
            # Read the test file back
            print(f"\nReading back test file '{test_file}'...")
            read_result = mcp.read_file(test_file)
            print(f"Content: {read_result.get('content')}")
            
            # Edit the test file
            print(f"\nEditing test file '{test_file}'...")
            edits = [
                {
                    "oldText": "This is a test file.",
                    "newText": "This is an edited test file."
                }
            ]
            edit_result = mcp.edit_file(test_file, edits)
            print(f"Edit success: {len(edit_result.get('appliedEdits', [])) > 0}")
            print(f"Diff: \n{edit_result.get('diff')}")
            
            # Read the edited file
            print(f"\nReading edited test file '{test_file}'...")
            read_result = mcp.read_file(test_file)
            print(f"Content: {read_result.get('content')}")
            
            # Search for files
            print("\nSearching for Python files...")
            search_result = mcp.search_files("*.py")
            matches = search_result.get('matches', [])
            print(f"Found {len(matches)} Python files:")
            for match in sorted(matches):
                print(f"  - {match}")
        
        else:
            print(f"\nCurrent file '{this_file}' not found in directory listing.")
    
    except Exception as e:
        print(f"Error testing filesystem: {e}")
        return

if __name__ == "__main__":
    test_filesystem() 