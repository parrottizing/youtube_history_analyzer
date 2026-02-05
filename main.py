
import subprocess
import sys
import os
import time

def run_step(script_path):
    print(f"\n{'='*50}")
    print(f"Running: {script_path}")
    print(f"{'='*50}\n")
    
    start_time = time.time()
    try:
        # Use the same python executable
        result = subprocess.run([sys.executable, script_path], check=True)
        elapsed = time.time() - start_time
        print(f"\nStep completed in {elapsed:.2f} seconds.")
    except subprocess.CalledProcessError as e:
        print(f"\nStep failed with return code {e.returncode}.")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

def main():
    print("Starting YouTube History Analysis Pipeline...")
    
    steps = [
        "steps/01_scrape_history.py",
        "steps/02_extract_ids.py",
        "steps/03_deduplicate.py",
        "steps/04_enrich_metadata.py",
        "steps/05_video_categorizer.py",
        "steps/06_visualize.py"
    ]
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    for step in steps:
        script_path = os.path.join(root_dir, step)
        if not os.path.exists(script_path):
            print(f"Error: Script not found: {script_path}")
            sys.exit(1)
            
        run_step(script_path)
        
    print("\n\nPipeline execution completed successfully!")
    print(f"Check the 'output' directory for results.")

if __name__ == "__main__":
    main()
