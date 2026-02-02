
import csv
import os
import sys
import json
import re
import urllib.request
import urllib.parse
import urllib.error
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.env_loader import load_env
except ImportError:
    from utils.env_loader import load_env

def parse_iso_duration(duration_str):
    """
    Parses ISO 8601 duration (e.g. PT1H2M10S) to HH:MM:SS or MM:SS.
    """
    if not duration_str:
        return ""
        
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    
    if not match:
        return duration_str
        
    h, m, s = match.groups()
    h = int(h) if h else 0
    m = int(m) if m else 0
    s = int(s) if s else 0
    
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    else:
        return f"{m}:{s:02d}"

def fetch_video_details_batch(video_ids, api_key):
    """
    Fetches details for a list of video IDs (max 50) using YouTube Data API.
    """
    if not video_ids:
        return {}
        
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,contentDetails",
        "id": ",".join(video_ids),
        "key": api_key
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        results = {}
        if "items" in data:
            for item in data["items"]:
                vid = item["id"]
                snippet = item.get("snippet", {})
                content_details = item.get("contentDetails", {})
                
                results[vid] = {
                    "Channel": snippet.get("channelTitle"),
                    "Duration": parse_iso_duration(content_details.get("duration")), # Converted from ISO 8601
                    "OriginalLanguage": snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage") or "Unknown",
                    "Title": snippet.get("title") # Update title from API as it's cleaner than scraped
                }
        return results
        
    except urllib.error.HTTPError as e:
        print(f"Error fetching batch: {e}")
        return {}

def main():
    print("Starting Metadata Enrichment (Step 4)...")
    load_env()
    api_key = os.getenv("YOU_TUBE_API_KEY")
    
    if not api_key:
        print("Error: YOU_TUBE_API_KEY not found in .env")
        return

    input_file = os.path.join("data", "03_unique_ids.csv")
    output_file = os.path.join("data", "04_enriched.csv")
    
    if not os.path.exists(input_file):
        print("Input file not found.")
        return
        
    # Read unique IDs
    videos_to_process = [] # List of dicts
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        videos_to_process = list(reader)
        
    enrichment_map = {}
    
    # Process in batches of 50
    batch_size = 50
    total_videos = len(videos_to_process)
    
    print(f"Processing {total_videos} videos in batches of {batch_size}...")
    
    for i in range(0, total_videos, batch_size):
        batch = videos_to_process[i:i+batch_size]
        batch_ids = [v['VideoID'] for v in batch]
        
        print(f"  Fetching batch {i//batch_size + 1} ({len(batch_ids)} videos)...")
        results = fetch_video_details_batch(batch_ids, api_key)
        enrichment_map.update(results)
        
        # Rate limit helpfulness
        time.sleep(0.5)
        
    # Merge data
    enriched_rows = []
    
    for row in videos_to_process:
        vid = row['VideoID']
        details = enrichment_map.get(vid)
        
        if details:
            # Update/Add fields
            row['Channel'] = details.get('Channel', '')
            row['Duration'] = details.get('Duration', '')
            row['OriginalLanguage'] = details.get('OriginalLanguage', '')
            # Optional: Overwrite title if API title is preferred
            row['Title'] = details.get('Title', row['Title']) 
        else:
            # Maybe deleted video or private?
            row['Channel'] = "Unknown"
            row['Duration'] = ""
            row['OriginalLanguage'] = "Unknown"
            
        enriched_rows.append(row)
        
    # Write output
    fieldnames = ['Date', 'Title', 'Link', 'VideoID', 'Channel', 'Duration', 'OriginalLanguage']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_rows)
        
    print(f"Enriched data saved to {output_file}")

if __name__ == "__main__":
    main()
