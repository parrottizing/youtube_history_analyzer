
import csv
import os
import re
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    Examples:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - https://youtu.be/VIDEO_ID
    """
    parsed = urlparse(url)
    
    # Standard watch URL
    if parsed.path == '/watch':
        return parse_qs(parsed.query).get('v', [None])[0]
    
    # Shorts URL
    if parsed.path.startswith('/shorts/'):
        return parsed.path.split('/')[2]
    
    # Shortened URL
    if parsed.netloc == 'youtu.be':
        return parsed.path[1:]
        
    return None

def main():
    print("Starting ID Extraction (Step 2)...")
    
    input_file = os.path.join("data", "01_raw_history.csv")
    output_file = os.path.join("data", "02_video_ids.csv")
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Run step 1 first.")
        return

    processed_count = 0
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', newline='', encoding='utf-8') as f_out:
        
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames + ['VideoID']
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            link = row.get('Link', '')
            video_id = extract_video_id(link)
            
            if video_id:
                row['VideoID'] = video_id
                writer.writerow(row)
                processed_count += 1
            else:
                # Could be a channel link or something else
                pass

    print(f"Extracted IDs for {processed_count} videos.")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
