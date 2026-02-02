
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import re
import numpy as np

# Fix Unicode encoding for Windows console (just in case)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Parsing ISO 8601 duration (PT1H2M10S) to seconds
def parse_iso_duration(duration_str):
    if not isinstance(duration_str, str) or not duration_str.startswith('PT'):
        return 0
    
    # Simple regex parsing
    # PT#H#M#S
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    
    if not match:
        return 0
        
    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0
    
    return hours * 3600 + minutes * 60 + seconds

def format_time_display(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

def main():
    print("Starting Visualization (Step 6)...")
    
    input_file = os.path.join("data", "05_categorized.csv")
    output_dir = "output"
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Run previous steps.")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Read data
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} records.")
    
    # Parse Duration
    df['DurationSeconds'] = df['Duration'].apply(parse_iso_duration)
    
    # Clean Language
    # Map 'en', 'en-US' -> 'English', 'ru' -> 'Russian'
    def map_language(lang):
        if not isinstance(lang, str): return 'Other'
        lang = lang.lower()
        if 'ru' in lang: return 'Russian'
        if 'en' in lang: return 'English'
        return 'Other'
        
    df['LangGroup'] = df['OriginalLanguage'].apply(map_language)
    
    # Filter out extremely short videos (e.g. < 30s) if wanted? 
    # User didn't ask, but good for analysis. I'll keep all.
    
    # Set style
    plt.style.use('default')
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
    
    # === Graph 1: Top Channels by Count ===
    try:
        top_channels = df['Channel'].value_counts().head(10)
        plt.figure(figsize=(12, 6))
        top_channels.plot(kind='bar', color='#4ECDC4', edgecolor='black')
        plt.title('Top 10 Channels by Video Count')
        plt.xlabel('Channel')
        plt.ylabel('Videos Watched')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '01_top_channels_count.png'), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Error Gen Graph 1: {e}")

    # === Graph 2: Top Channels by Time ===
    try:
        time_by_channel = df.groupby('Channel')['DurationSeconds'].sum().sort_values(ascending=False).head(10)
        plt.figure(figsize=(12, 6))
        # Convert to hours
        (time_by_channel / 3600).plot(kind='bar', color='#FF6B6B', edgecolor='black')
        plt.title('Top 10 Channels by Watch Time (Hours)')
        plt.xlabel('Channel')
        plt.ylabel('Hours')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '02_top_channels_time.png'), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Error Gen Graph 2: {e}")

    # === Graph 3: Categories by Count ===
    try:
        cat_counts = df['Category'].value_counts().head(10)
        plt.figure(figsize=(12, 6))
        cat_counts.plot(kind='bar', color='#C7F464', edgecolor='black')
        plt.title('Top Categories by Video Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '03_categories_count.png'), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Error Gen Graph 3: {e}")

    # === Graph 4: Categories by Time ===
    try:
        cat_time = df.groupby('Category')['DurationSeconds'].sum().sort_values(ascending=False).head(10)
        plt.figure(figsize=(12, 6))
        (cat_time / 3600).plot(kind='bar', color='#FFCC5C', edgecolor='black')
        plt.title('Top Categories by Watch Time (Hours)')
        plt.ylabel('Hours')
        plt.xticks(rotation=45, ha='right')
        # Add labels
        ax = plt.gca()
        for p in ax.patches:
            ax.annotate(f'{p.get_height():.1f}h', (p.get_x() + p.get_width() / 2., p.get_height()), 
                        ha='center', va='bottom')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '04_categories_time.png'), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Error Gen Graph 4: {e}")
        
    print(f"Graphs saved to {output_dir}/")

if __name__ == "__main__":
    main()
