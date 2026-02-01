#!/usr/bin/env python3
"""
Script to get the original language of a YouTube video using the YouTube Data API.
Uses only standard library to avoid dependency issues.
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error

def load_env():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove surrounding quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value

def get_video_language(video_id: str) -> dict:
    """
    Fetch video details from YouTube Data API and return language information.
    
    Args:
        video_id: The YouTube video ID
        
    Returns:
        Dictionary containing language information
    """
    api_key = os.getenv("YOU_TUBE_API_KEY")
    if not api_key:
        raise ValueError("YOU_TUBE_API_KEY not found in environment variables")
    
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": api_key
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP Error {e.code}: {e.reason}")
        print(f"Response: {error_body}")
        raise
    
    if not data.get("items"):
        return {"error": "Video not found"}
    
    snippet = data["items"][0]["snippet"]
    
    return {
        "video_id": video_id,
        "title": snippet.get("title"),
        "defaultLanguage": snippet.get("defaultLanguage"),
        "defaultAudioLanguage": snippet.get("defaultAudioLanguage"),
    }


if __name__ == "__main__":
    # Load .env file
    load_env()
    
    video_id = "WwI9_WA6pHc"
    
    result = get_video_language(video_id)
    
    print(f"Video ID: {result.get('video_id')}")
    print(f"Title: {result.get('title')}")
    print(f"Default Language: {result.get('defaultLanguage')}")
    print(f"Default Audio Language: {result.get('defaultAudioLanguage')}")
