#!/usr/bin/env python
import os
import sys

def setup_path():
    """Add the parent directory to Python path for proper imports"""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        print(f"Added {parent_dir} to Python path for imports")
    return parent_dir

if __name__ == "__main__":
    setup_path()
    print(f"Current Python path: {sys.path}") 