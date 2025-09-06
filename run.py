#!/usr/bin/env python3
"""
Script to run the Calendar Diagonal Spread Analyzer Streamlit app.
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit app."""
    try:
        # Check if we're in a Poetry environment
        if 'VIRTUAL_ENV' in os.environ:
            print("Running in Poetry virtual environment...")
        
        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nApp stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit app: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 