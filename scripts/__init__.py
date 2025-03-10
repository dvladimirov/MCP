#!/usr/bin/env python3
"""
MCP Scripts Package

This package contains scripts and utilities for the MCP (Model Control Plane) system.
"""

import os
import sys

# Add the parent directory to Python path for proper imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir) 