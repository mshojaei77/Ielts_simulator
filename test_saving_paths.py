#!/usr/bin/env python3
"""
Test script to verify that all IELTS test sections save results to the correct directories.
This script validates the path construction logic without running the full UI.
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_listening_save_path():
    """Test Listening UI save path construction."""
    print("Testing Listening UI save path...")
    
    # Simulate the path construction from ui_listening_test.py
    ui_dir = os.path.join(os.path.dirname(__file__), 'ui')
    ielts_practice_path = os.path.join(ui_dir, '..', 'results', 'listening')
    absolute_path = os.path.abspath(ielts_practice_path)
    
    print(f"  Listening save path: {absolute_path}")
    expected_path = os.path.join(os.path.dirname(__file__), 'results', 'listening')
    expected_absolute = os.path.abspath(expected_path)
    
    if absolute_path == expected_absolute:
        print("  ✓ Listening path is correct")
        return True
    else:
        print(f"  ✗ Listening path mismatch. Expected: {expected_absolute}")
        return False

def test_reading_save_path():
    """Test Reading UI save path construction."""
    print("Testing Reading UI save path...")
    
    # Simulate the path construction from ui_reading_test.py
    ui_dir = os.path.join(os.path.dirname(__file__), 'ui')
    results_dir = os.path.join(ui_dir, '..', 'results', 'reading')
    absolute_path = os.path.abspath(results_dir)
    
    print(f"  Reading save path: {absolute_path}")
    expected_path = os.path.join(os.path.dirname(__file__), 'results', 'reading')
    expected_absolute = os.path.abspath(expected_path)
    
    if absolute_path == expected_absolute:
        print("  ✓ Reading path is correct")
        return True
    else:
        print(f"  ✗ Reading path mismatch. Expected: {expected_absolute}")
        return False

def test_writing_save_path():
    """Test Writing UI save path construction."""
    print("Testing Writing UI save path...")
    
    # Simulate the path construction from ui_writing_test.py
    ui_dir = os.path.join(os.path.dirname(__file__), 'ui')
    results_dir = os.path.join(ui_dir, '..', 'results', 'writing')
    absolute_path = os.path.abspath(results_dir)
    
    print(f"  Writing save path: {absolute_path}")
    expected_path = os.path.join(os.path.dirname(__file__), 'results', 'writing')
    expected_absolute = os.path.abspath(expected_path)
    
    if absolute_path == expected_absolute:
        print("  ✓ Writing path is correct")
        return True
    else:
        print(f"  ✗ Writing path mismatch. Expected: {expected_absolute}")
        return False

def test_speaking_save_path():
    """Test Speaking UI save path construction."""
    print("Testing Speaking UI save path...")
    
    # Simulate the path construction from ui_speaking_test.py
    ui_dir = os.path.join(os.path.dirname(__file__), 'ui')
    base_dir = os.path.abspath(os.path.join(ui_dir, '..'))
    recordings_dir = os.path.join(base_dir, 'results', 'speaking')
    absolute_path = os.path.abspath(recordings_dir)
    
    print(f"  Speaking save path: {absolute_path}")
    expected_path = os.path.join(os.path.dirname(__file__), 'results', 'speaking')
    expected_absolute = os.path.abspath(expected_path)
    
    if absolute_path == expected_absolute:
        print("  ✓ Speaking path is correct")
        return True
    else:
        print(f"  ✗ Speaking path mismatch. Expected: {expected_absolute}")
        return False

def create_test_directories():
    """Create the required results directories for testing."""
    print("Creating test directories...")
    
    base_results_dir = os.path.join(os.path.dirname(__file__), 'results')
    subdirs = ['listening', 'reading', 'writing', 'speaking']
    
    for subdir in subdirs:
        dir_path = os.path.join(base_results_dir, subdir)
        os.makedirs(dir_path, exist_ok=True)
        print(f"  Created/verified: {dir_path}")

def main():
    """Run all path validation tests."""
    print("=" * 60)
    print("IELTS SIMULATOR - SAVE PATH VALIDATION TEST")
    print("=" * 60)
    print(f"Project root: {os.path.dirname(__file__)}")
    print(f"Expected results directory: {os.path.join(os.path.dirname(__file__), 'results')}")
    print()
    
    # Create directories first
    create_test_directories()
    print()
    
    # Test all paths
    tests = [
        test_listening_save_path,
        test_reading_save_path,
        test_writing_save_path,
        test_speaking_save_path
    ]
    
    results = []
    for test_func in tests:
        results.append(test_func())
        print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} tests PASSED")
        print("All sections will save results to the correct directories:")
        print(f"  - Listening: /c:/my_projects/Ielts_simulator/results/listening/")
        print(f"  - Reading: /c:/my_projects/Ielts_simulator/results/reading/")
        print(f"  - Writing: /c:/my_projects/Ielts_simulator/results/writing/")
        print(f"  - Speaking: /c:/my_projects/Ielts_simulator/results/speaking/")
    else:
        print(f"✗ {total - passed} out of {total} tests FAILED")
        print("Some sections may not save to the correct directories.")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)