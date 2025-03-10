#!/usr/bin/env python
import os
import sys

# Add the parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

print(f"Added {parent_dir} to Python path")
print(f"Current Python path: {sys.path}") 