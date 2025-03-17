import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp.filesystem_service import FilesystemService

class TestFilesystemService:
    """Tests for the FilesystemService class"""
    
    @pytest.fixture
    def fs_service(self):
        """Create a FilesystemService instance for testing"""
        service = FilesystemService()
        # Patch the _is_path_allowed method to always return True for tests
        with patch.object(service, '_is_path_allowed', return_value=True):
            yield service
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for file operations"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after tests
        shutil.rmtree(temp_dir)
    
    def test_list_directory(self, fs_service, temp_dir):
        """Test listing directory contents"""
        # Create test files and directories
        test_file1 = Path(temp_dir) / "test1.txt"
        test_file1.touch()
        
        test_file2 = Path(temp_dir) / "test2.py"
        test_file2.touch()
        
        test_subdir = Path(temp_dir) / "subdir"
        test_subdir.mkdir()
        
        # Test the list_directory method
        result = fs_service.list_directory(temp_dir)
        
        # Verify results - we should have 3 entries (2 files and 1 directory)
        assert len(result) == 3
        
        # Check that each entry has the expected structure
        file_names = [entry["name"] for entry in result]
        assert "test1.txt" in file_names
        assert "test2.py" in file_names
        assert "subdir" in file_names
        
        # Check for correct type classification
        dir_entries = [entry for entry in result if entry["type"] == "DIR"]
        file_entries = [entry for entry in result if entry["type"] == "FILE"]
        assert len(dir_entries) == 1
        assert len(file_entries) == 2
    
    def test_read_file(self, fs_service, temp_dir):
        """Test reading a file's contents"""
        # Create a test file with content
        test_file = Path(temp_dir) / "test_read.txt"
        test_content = "This is a test file content."
        test_file.write_text(test_content)
        
        # Test the read_file method
        result = fs_service.read_file(str(test_file))
        
        # Verify results - the result should be the content string
        assert result == test_content
    
    def test_write_file(self, fs_service, temp_dir):
        """Test writing content to a file"""
        # Define the file path and content
        test_file = Path(temp_dir) / "test_write.txt"
        test_content = "This is new content to write."
        
        # Test the write_file method
        result = fs_service.write_file(str(test_file), test_content)
        
        # Verify results - result should be a dictionary with success information
        assert "path" in result
        assert "size" in result
        assert test_file.exists()
        assert test_file.read_text() == test_content
    
    def test_edit_file(self, fs_service, temp_dir):
        """Test editing an existing file"""
        # Create a test file with initial content
        test_file = Path(temp_dir) / "test_edit.txt"
        initial_content = "Line 1\nLine 2\nLine 3\nLine 4\n"
        test_file.write_text(initial_content)
        
        # Define edits with oldText/newText format
        edits = [
            {"oldText": "Line 1", "newText": "Modified Line 1"},
            {"oldText": "Line 3", "newText": "Modified Line 3"}
        ]
        
        # Test the edit_file method
        result = fs_service.edit_file(str(test_file), edits)
        
        # Verify results - result should be a dictionary with diff information
        assert "diff" in result
        
        # Read the updated file content
        updated_content = test_file.read_text()
        expected_content = "Modified Line 1\nLine 2\nModified Line 3\nLine 4\n"
        assert updated_content == expected_content
    
    def test_create_directory(self, fs_service, temp_dir):
        """Test creating a directory"""
        # Define directory path
        test_dir = Path(temp_dir) / "new_directory"
        
        # Test the create_directory method
        result = fs_service.create_directory(str(test_dir))
        
        # Verify results
        assert result["success"] is True
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_move_file(self, fs_service, temp_dir):
        """Test moving a file from source to destination"""
        # Create a test file
        source_file = Path(temp_dir) / "source.txt"
        source_content = "This is the source file."
        source_file.write_text(source_content)
        
        # Define destination path
        dest_file = Path(temp_dir) / "destination.txt"
        
        # Test the move_file method
        result = fs_service.move_file(str(source_file), str(dest_file))
        
        # Verify results
        assert result["success"] is True
        assert not source_file.exists()
        assert dest_file.exists()
        assert dest_file.read_text() == source_content
    
    def test_search_files(self, fs_service, temp_dir):
        """Test searching for files matching a pattern"""
        # Create test files
        test_py1 = Path(temp_dir) / "test1.py"
        test_py1.touch()
        
        test_py2 = Path(temp_dir) / "test2.py"
        test_py2.touch()
        
        test_txt = Path(temp_dir) / "test.txt"
        test_txt.touch()
        
        # Create a subdirectory with a matching file
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        test_py3 = subdir / "test3.py"
        test_py3.touch()
        
        # Test the search_files method
        result = fs_service.search_files(temp_dir, "*.py")
        
        # Verify results - result should be a list of file paths
        assert len(result) == 3
        
        # Convert paths to strings for easier comparison
        paths = [str(p) for p in result]
        assert str(test_py1) in paths
        assert str(test_py2) in paths
        assert str(test_py3) in paths
        assert str(test_txt) not in paths
    
    def test_get_file_info(self, fs_service, temp_dir):
        """Test getting file information"""
        # Create a test file
        test_file = Path(temp_dir) / "test_info.txt"
        test_content = "This is a test file."
        test_file.write_text(test_content)
        
        # Test the get_file_info method
        result = fs_service.get_file_info(str(test_file))
        
        # Verify results - result should have file metadata
        assert "name" in result
        assert result["name"] == "test_info.txt"
        assert "size" in result
        assert result["size"] >= len(test_content)
        assert "modified" in result 