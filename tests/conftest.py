"""
tests/conftest.py
Shared pytest configuration and fixtures for VendorMind AI test suite.
"""
import sys
from pathlib import Path

# Ensure the project root is on the Python path for all test modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
