#!/usr/bin/env python3
"""
YouTube History Analyzer - Full Pipeline Runner

This script runs the complete YouTube history analysis pipeline from start to finish.
It executes all processing scripts in the correct order and provides progress feedback.

Usage:
    python run_pipeline.py

Requirements:
    - history.txt file in the project root
    - .env file with GEMINI_API_KEY configured
    - All required dependencies installed
"""

import subprocess
import sys
import os
import time
from pathlib import Path

# Fix Unicode encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def run_script(script_name, description):
    """Run a Python script and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"{description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Use subprocess.Popen for real-time output
        process = subprocess.Popen([sys.executable, script_name], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True,
                                 bufsize=1,
                                 universal_newlines=True)
        
        # Read output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                sys.stdout.flush()  # Ensure immediate output
        
        # Get return code
        return_code = process.poll()
        
        elapsed = time.time() - start_time
        
        if return_code == 0:
            print(f"\n✅ {script_name} completed successfully in {elapsed:.1f}s")
            return True
        else:
            # Read any remaining stderr
            stderr_output = process.stderr.read()
            print(f"\n❌ {script_name} failed after {elapsed:.1f}s")
            if stderr_output:
                print(f"Error: {stderr_output.strip()}")
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ {script_name} failed after {elapsed:.1f}s")
        print(f"Error: {e}")
        return False

def check_prerequisites():
    """Check if all required files and dependencies exist."""
    print("Checking prerequisites...")
    
    # Check for input file
    if not os.path.exists("history.txt"):
        print("Missing required file: history.txt")
        print("Please place your YouTube history export in the project root.")
        return False
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("Missing required file: .env")
        print("Please create .env file with GEMINI_API_KEY configured.")
        return False
    
    print("All prerequisites found")
    return True

def main():
    """Run the complete YouTube history analysis pipeline."""
    print("YouTube History Analyzer - Full Pipeline")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\nPipeline aborted due to missing prerequisites")
        sys.exit(1)
    
    # Define pipeline steps
    pipeline_steps = [
        ("parser.py", "Parse raw history.txt to youtube_history.csv"),
        ("remove_duplicates.py", "Remove duplicates -> youtube_history_clean.csv"),
        ("add_language_column.py", "Add language detection -> youtube_history_with_language.csv"),
        ("analyze_by_channels.py", "Generate channel analysis CSVs"),
        ("add_categories.py", "AI categorization -> youtube_history_with_categories.csv"),
        ("create_graphs.py", "Create channel/language graphs"),
        ("create_category_graphs.py", "Create category analysis graphs")
    ]
    
    print(f"\nStarting pipeline with {len(pipeline_steps)} steps...")
    
    start_time = time.time()
    failed_steps = []
    
    # Execute each step
    for i, (script, description) in enumerate(pipeline_steps, 1):
        print(f"\nStep {i}/{len(pipeline_steps)}")
        
        if not run_script(script, description):
            failed_steps.append(script)
            print(f"\nPipeline failed at step {i}: {script}")
            break
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print("PIPELINE SUMMARY")
    print(f"{'='*60}")
    
    if failed_steps:
        print(f"Pipeline failed after {total_time/60:.1f} minutes")
        print(f"Failed step: {failed_steps[0]}")
        print("\nTo continue from where it left off, run the remaining scripts manually.")
        sys.exit(1)
    else:
        print(f"Pipeline completed successfully in {total_time/60:.1f} minutes!")
        print("\nGenerated files:")
        print("   * youtube_history_with_categories.csv (final data)")
        print("   * channel_analysis.csv (channel statistics)")
        print("   * videos_by_channel.csv (detailed video listings)")
        print("   * 6 visualization graphs (PNG files)")
        print("\nYour YouTube history analysis is ready!")

if __name__ == "__main__":
    main()