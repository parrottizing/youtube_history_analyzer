# YouTube Transcript Fetching Strategy

## Objective
Fetch transcripts for ~150 YouTube videos quickly, reliably, and without polluting the user's watch history.

## Constraints & Requirements
*   **Speed**: Bulk processing (~150 videos) should happen in minutes.
*   **Privacy**: MUST NOT affect YouTube watch history.
*   **Reliability**: Minimize 429 (Too Many Requests) errors and IP bans.
*   **Context**: Codebase context was broken; built a fresh, standalone solution (`fetch_transcripts.py`).

## Implementation Details (Final)

### 1. Hybrid Fetching Approach
We implemented a robust `TranscriptFetcher` class in `fetch_transcripts.py` that prioritizes speed but has deep fallbacks:
*   **Step 1: `youtube_transcript_api` (Instance Mode)**:
    *   Instantiates `YouTubeTranscriptApi` (required for v0.6+).
    *   Uses `.list(video_id)` to get available transcripts.
    *   **Cookie-less by default**: Prevents history pollution.
*   **Step 2: Fallback to `yt-dlp`**:
    *   If API fails (e.g., severe IP blocking beyond simple rate limiting), we invoke `yt-dlp`.
    *   **Cookie Support**: Added `--cookies` argument. This is critical for cloud environments (AWS/GCP/VPS) where YouTube blocks anonymous requests. `yt-dlp` with cookies bypasses this while subtitle fetching generally doesn't count as a "watch".

### 2. Smart Language Handling
To maximize success rate (avoiding empty files), we implemented a cascading language logic:
1.  **Direct English**: Search for manually created or auto-generated 'en' transcript.
2.  **Any Transcript**: If English missing, grab *any* available transcript (e.g., the original language).
3.  **Translation**: Attempt to translate that transcript to English via the API.
4.  **Original Fallback**: If translation fails, save the original text (e.g., Korean) so we at least have data.

### 3. Data Source Integration
*   **Input File**: The script reads from `data/04_enriched.csv`.
*   **Columns**: Identifies videos using `VideoID` or `Link` columns.
*   **Output**: Saves plain text files to `data/transcripts/{VideoID}.txt`.

### 4. Error Handling & Rate Limits
*   **Exponential Backoff**: On 429 (Too Many Requests) errors.
*   **Jittered Sleep**: Random delays (2-5s) between requests.
*   **Detection**: String matching for "Too many requests" in exception messages (since `youtube_transcript_api` v0.6+ dropped the explicit exception class).

## Usage
```bash
# Basic run (if IP is clean)
python3 fetch_transcripts.py --csv data/04_enriched.csv

# Run with cookies (Recommended for 100% success)
python3 fetch_transcripts.py --csv data/04_enriched.csv --cookies cookies.txt
```
