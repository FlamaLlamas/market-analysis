#!/usr/bin/env python3
"""
Test script for synthetic options generator
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from synthetic_options_generator import main
import subprocess

def test_synthetic_generation():
    """Test synthetic options generation for a few days"""
    print("🧪 Testing Synthetic Options Generation")
    print("=" * 50)
    
    # Test with 5 days of data
    cmd = [
        'python', 'data_fetcher/src/synthetic_options_generator.py',
        '^SPX',
        '--test-days', '5',
        '--volatility-window', '30',
        '--risk-free-rate', '0.05'
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Synthetic options generation test completed successfully!")
        else:
            print(f"❌ Test failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running test: {e}")

if __name__ == '__main__':
    test_synthetic_generation()
