import os
import time
import random
import logging
import argparse
import glob
import pandas as pd
import requests
import http.cookiejar
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.formatters import TextFormatter
import yt_dlp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("transcript_fetch.log"),
        logging.StreamHandler()
    ]
)

class TranscriptFetcher:
    def __init__(self, output_dir="data/transcripts", cookie_file=None, safe_mode=False, min_sleep=None, max_sleep=None):
        self.output_dir = output_dir
        self.cookie_file = cookie_file
        self.safe_mode = safe_mode
        self.yt_api = YouTubeTranscriptApi()
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set sleep times
        if min_sleep is not None:
            self.min_sleep = float(min_sleep)
        else:
             self.min_sleep = 5.0 if self.safe_mode else 2.0

        if max_sleep is not None:
             self.max_sleep = float(max_sleep)
        else:
             self.max_sleep = 10.0 if self.safe_mode else 5.0

        # Configure Session with Cookies if provided
        self.http_session = requests.Session()
        self.http_session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        if self.cookie_file and os.path.exists(self.cookie_file):
            try:
                cj = http.cookiejar.MozillaCookieJar(self.cookie_file)
                cj.load(ignore_discard=True, ignore_expires=True)
                self.http_session.cookies = cj
                logging.info(f"Loaded cookies from {self.cookie_file} for Main API")
            except Exception as e:
                logging.error(f"Failed to load cookie file: {e}")

        self.yt_api = YouTubeTranscriptApi(http_client=self.http_session)

    def get_video_id(self, url):
        """Extracts video ID from various YouTube URL formats."""
        if len(url) == 11 and ' ' not in url and '/' not in url:
            return url # It's probably an ID
            
        parsed_url = urlparse(url)
        if parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                p = parse_qs(parsed_url.query)
                return p['v'][0]
            if parsed_url.path[:7] == '/embed/':
                return parsed_url.path.split('/')[2]
            if parsed_url.path[:3] == '/v/':
                return parsed_url.path.split('/')[2]
        # Fail gracefully
        return None

    def fetch_with_api(self, video_id):
        """Attempts to fetch transcript using youtube_transcript_api."""
        try:
            # Prefer manually created English, fallback to automated English
            transcript_list = self.yt_api.list(video_id)
            
            # 1. Try English directly (Manual or Auto)
            try:
                transcript = transcript_list.find_transcript(['en'])
                return transcript.fetch()
            except NoTranscriptFound:
                pass

            # 2. If no English, take the first available transcript
            try:
                # This gets you the first available transcript (manual or auto)
                # Iterating over transcript_list gives all available transcripts
                first_transcript = next(iter(transcript_list))
            except StopIteration:
                logging.warning(f"No transcripts found at all for {video_id}")
                return None

            # 3. Try to translate it to English (SKIP IN SAFE MODE)
            if not self.safe_mode and first_transcript.is_translatable:
                try:
                    translated = first_transcript.translate('en')
                    logging.info(f"Translated {first_transcript.language_code} to English for {video_id}")
                    return translated.fetch()
                except Exception as e:
                     logging.warning(f"Translation failed for {video_id}: {e}")
            
            # 4. Fallback: Return original language
            logging.info(f"Falling back to original language {first_transcript.language_code} for {video_id}")
            return first_transcript.fetch()
            
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            logging.warning(f"API Method failed for {video_id}: {e}")
            return None
        except Exception as e:
            if "Too many requests" in str(e) or "429" in str(e):
                raise # Let fetch_one handle backoff
            logging.error(f"Unexpected API error for {video_id}: {e}")
            return None

    def fetch_with_ytdlp(self, video_id):
        """Fallback method using yt-dlp."""
        logging.info(f"Attempting yt-dlp fallback for {video_id}...")
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        ydl_opts = {
            'skip_download': True,
            'writeautomaticsub': True,
            'writesubtitles': True,
            'subtitleslangs': ['en'],
            'outtmpl': f'{self.output_dir}/temp_{video_id}',
            'quiet': True,
            'no_warnings': True,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': self.cookie_file, 
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded file
            files = glob.glob(f'{self.output_dir}/temp_{video_id}.*.vtt')
            if not files:
                 files = glob.glob(f'{self.output_dir}/temp_{video_id}.*.srt')
            
            if files:
                # Read content and clean up
                content = ""
                file_path = files[0]
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Cleanup temp files
                for f in files:
                    os.remove(f)
                    
                return [{'text': content, 'start': 0, 'duration': 0}] # Mock structure for raw text
            
            return None
        except Exception as e:
            logging.error(f"yt-dlp failed for {video_id}: {e}")
            return None

    def save_transcript(self, video_id, data):
        """Saves transcript to a file."""
        file_path = os.path.join(self.output_dir, f"{video_id}.txt")
        
        full_text = ""
        # data is a list of dicts {'text': '...', 'start': ..., 'duration': ...}
        # OR raw text from yt-dlp fallback
        
        if isinstance(data, list):
             # Fallback/yt-dlp structure
             text_parts = [item['text'].replace('\n', ' ') for item in data]
             full_text = " ".join(text_parts)
        elif hasattr(data, 'snippets'):
             # YouTubeTranscriptApi FetchedTranscript object
             text_parts = [snippet.text.replace('\n', ' ') for snippet in data.snippets]
             full_text = " ".join(text_parts)
        else:
             full_text = str(data)

        with open(file_path, "w", encoding='utf-8') as f:
            f.write(full_text)
        
        logging.info(f"Saved transcript for {video_id} to {file_path}")

    def fetch_one(self, start_url):
        video_id = self.get_video_id(start_url)
        if not video_id:
            logging.error(f"Invalid URL: {start_url}")
            return False

         # Exponential backoff parameters
        retries = 3
        wait_time = 300 if self.safe_mode else 10 

        for attempt in range(retries):
            try:
                # 1. Try API
                data = self.fetch_with_api(video_id)
                
                # 2. Try yt-dlp if API failed (but not because of blocking)
                if not data:
                    data = self.fetch_with_ytdlp(video_id)
                
                if data:
                    self.save_transcript(video_id, data)
                    return True
                else:
                    logging.warning(f"Could not fetch transcript for {video_id} with any method.")
                    return False

            except Exception as e:
                error_msg = str(e).lower()
                if "too many requests" in error_msg or "429" in error_msg:
                    logging.warning(f"429 Too Many Requests for {video_id}. Sleeping {wait_time}s...")
                    time.sleep(wait_time)
                    wait_time *= 2 # Exponential backoff
                    continue
                
                logging.error(f"Critical error processing {video_id}: {e}")
                return False
        
        return False

    def process_list(self, urls, burst_mode=False):
        count = 0
        total = len(urls)
        
        # Burst settings
        batch_size = 5
        cooldown_time = 60
        processed_in_batch = 0

        for url in urls:
            count += 1
            logging.info(f"Processing {count}/{total}: {url}")
            
            # Check if file exists
            video_id = self.get_video_id(url)
            if video_id:
                outfile = os.path.join(self.output_dir, f"{video_id}.txt")
                if os.path.exists(outfile) and os.path.getsize(outfile) > 0:
                     logging.info(f"Skipping {video_id} (already exists)")
                     continue
            
            self.fetch_one(url)
            
            # Sleep Logic
            processed_in_batch += 1
            
            if burst_mode and processed_in_batch >= batch_size:
                logging.info(f"Batch limit ({batch_size}) reached. Cooling down for {cooldown_time}s...")
                time.sleep(cooldown_time)
                processed_in_batch = 0 # Reset batch counter
            else:
                # Jittered sleep (standard)
                sleep_time = random.uniform(self.min_sleep, self.max_sleep)
                logging.info(f"Sleeping {sleep_time:.2f}s...")
                time.sleep(sleep_time)

def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube transcripts without login.")
    parser.add_argument("--test", action="store_true", help="Run a test with pre-defined videos")
    parser.add_argument("--file", type=str, help="Path to file containing YouTube URLs (one per line)")
    parser.add_argument("--csv", type=str, help="Path to CSV file containing 'VideoID' or 'Link' column")
    parser.add_argument("--url", type=str, help="Single URL to fetch")
    parser.add_argument("--cookies", type=str, help="Path to cookies.txt file")
    parser.add_argument("--safe", action="store_true", help="Enable Safe Mode: no api translation, moderate delays (5-10s)")
    parser.add_argument("--min-sleep", type=float, help="Minimum sleep time in seconds")
    parser.add_argument("--max-sleep", type=float, help="Maximum sleep time in seconds")
    parser.add_argument("--burst-mode", action="store_true", help="Enable Burst Mode: 5 videos then 60s sleep")
    
    args = parser.parse_args()
    
    fetcher = TranscriptFetcher(
        cookie_file=args.cookies, 
        safe_mode=args.safe,
        min_sleep=args.min_sleep,
        max_sleep=args.max_sleep
    )
    
    if args.test:
        test_urls = [
            "https://www.youtube.com/watch?v=jNQXAC9IVRw", # Me at the zoo (Short, likely has subs)
            "https://www.youtube.com/watch?v=9bZkp7q19f0", # Gangnam Style (Popular, has subs)
        ]
        fetcher.process_list(test_urls, burst_mode=args.burst_mode)
    elif args.url:
        fetcher.process_list([args.url], burst_mode=args.burst_mode)
    elif args.file:
        if os.path.exists(args.file):
            with open(args.file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            fetcher.process_list(urls, burst_mode=args.burst_mode)
        else:
            logging.error(f"File not found: {args.file}")
    elif args.csv:
        if os.path.exists(args.csv):
            try:
                df = pd.read_csv(args.csv)
                if 'VideoID' in df.columns:
                     # Use VideoID directly
                     urls = df['VideoID'].dropna().astype(str).tolist()
                     logging.info(f"Loaded {len(urls)} VideoIDs from {args.csv}")
                     fetcher.process_list(urls, burst_mode=args.burst_mode)
                elif 'Link' in df.columns:
                     urls = df['Link'].dropna().astype(str).tolist()
                     logging.info(f"Loaded {len(urls)} Links from {args.csv}")
                     fetcher.process_list(urls, burst_mode=args.burst_mode)
                else:
                     logging.error(f"CSV must contain 'VideoID' or 'Link' column. Found: {df.columns.tolist()}")
            except Exception as e:
                logging.error(f"Error reading CSV: {e}")
        else:
            logging.error(f"CSV file not found: {args.csv}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
