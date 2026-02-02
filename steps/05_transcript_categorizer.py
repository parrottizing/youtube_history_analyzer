
import csv
import os
import sys
import json
import time
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.env_loader import load_env
except ImportError:
    from utils.env_loader import load_env

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("Error: youtube_transcript_api not installed. Please run: pip install youtube-transcript-api")
    YouTubeTranscriptApi = None

try:
    from groq import Groq
except ImportError:
    print("Error: groq not installed. Please run: pip install groq")
    Groq = None

def get_transcript_text(video_id):
    if not YouTubeTranscriptApi:
        return None
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # Combine text
        full_text = " ".join([item['text'] for item in transcript])
        return full_text
    except Exception:
        # No transcript or disabled
        return None

def classify_with_llm(client, text, categories):
    if not client or not text:
        return "Unknown"
        
    # Truncate text to fit context window (approx 4000 chars is safe for most)
    truncated_text = text[:4000]
    
    categories_str = ", ".join(categories)
    prompt = f"""
    Analyze the following YouTube video transcript and classify it into EXACTLY ONE of these categories:
    [{categories_str}]
    
    Transcript:
    {truncated_text}
    
    Return only the category name. If none fit perfectly, pick the closest one or "OTHER".
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-70b-8192", # Versatile model on Groq
            temperature=0.1,
        )
        result = chat_completion.choices[0].message.content.strip()
        
        # Clean up result (remove punctuation etc if LLM is chatty)
        for cat in categories:
            if cat.lower() == result.lower():
                return cat
        
        # Fuzzy match or just return result if it looks like a category
        return result
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return "Unknown"

def main():
    print("Starting Categorization (Step 5)...")
    load_env()
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY not found in .env. LLM features will be disabled.")
        client = None
    else:
        if Groq:
            client = Groq(api_key=api_key)
        else:
            client = None

    # Load Channel Map
    start_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    categories_file = os.path.join(start_dir, "channel_categories.json")
    
    channel_map = {}
    valid_categories = set(["OTHER", "AI AND CODING", "HUMOR", "F1", "POPULAR SCIENCE", "NEWS", "FOOTBALL", "BASKETBALL", "HISTORY", "SUPERHEROES"]) # Defaults
    
    if os.path.exists(categories_file):
        try:
            with open(categories_file, 'r', encoding='utf-8') as f:
                channel_map = json.load(f)
                # Update valid categories from file
                valid_categories.update(channel_map.values())
        except Exception as e:
            print(f"Error loading categories file: {e}")
            
    sorted_categories = sorted(list(valid_categories))
    
    input_file = os.path.join("data", "04_enriched.csv")
    output_file = os.path.join("data", "05_categorized.csv")
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found.")
        return

    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    total = len(rows)
    print(f"Processing {total} videos...")
    
    categorized_rows = []
    llm_count = 0
    map_count = 0
    
    for i, row in enumerate(rows):
        channel = row.get('Channel', '').strip()
        vid = row.get('VideoID', '')
        title = row.get('Title', '')
        
        category = "Unknown"
        
        # Strategy: Map -> LLM
        if channel in channel_map:
            category = channel_map[channel]
            map_count += 1
            print(f"[{i+1}/{total}] {channel} -> {category} (Map)")
        else:
            # Try LLM
            if client and vid and YouTubeTranscriptApi:
                print(f"[{i+1}/{total}] Fetching transcript for {vid} ({title})...")
                transcript_text = get_transcript_text(vid)
                if transcript_text:
                    category = classify_with_llm(client, transcript_text, sorted_categories)
                    print(f"  -> Classified as: {category}")
                    llm_count += 1
                    # Optional: Add to map to cache for this run?
                    # channel_map[channel] = category 
                else:
                    print(f"  -> No transcript found.")
                    category = "OTHER" # Default fallback
            else:
                category = "OTHER"
                
        row['Category'] = category
        categorized_rows.append(row)
        
        # Rate limit for LLM
        if client and channel not in channel_map and YouTubeTranscriptApi:
             time.sleep(1) # Groq is fast but has limits

    # Save
    fieldnames = list(rows[0].keys())
    if 'Category' not in fieldnames:
        fieldnames.append('Category')
        
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(categorized_rows)
        
    print(f"Done. Map matched: {map_count}, LLM categorized: {llm_count}")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
