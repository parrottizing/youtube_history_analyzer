# YouTube Transcript Fetching Strategy

## Objective
Fetch transcripts for ~150 YouTube videos quickly, reliably, and without polluting the user's watch history.

## Status Update (2026-02-02) - CRITICAL FINDINGS (Iterative)
1.  **Translation Trigger**: Confirmed that API-based translation triggers immediate blocks.
2.  **IP Reputation / Token Bucket**:
    *   Even with "Safe Mode" (No translation, 6-9s delay), the script successfully fetched **~13 videos** before hitting a hard 429 (Too Many Requests) wall.
    *   This indicates the IP address has a "allowance" or "reputation bucket" that fills up slowly. Once drained, even requests with cookies are blocked.
    *   `yt-dlp` fallback also fails when the IP is in this state.

## Revised Strategy: "Smart Burst Mode"

To balance "Speed" vs "Block Avoidance", we cannot use a fixed delay. We need a variable schedule that mimics human browsing sessions (watch a few, take a break).

### 1. Burst Processing
*   **Logic**: Fetch a small batch (e.g., 5-10 videos) relatively quickly (3-5s delay).
*   **Cooldown**: After the batch, force a **long sleep** (e.g., 60-120 seconds) to let the "token bucket" replenish.
*   **Why**: This is faster than a constant 30s delay (which totals ~75 mins) but safer than a constant 5s delay (which gets blocked after 13 videos).

### 2. IP Hygiene
*   **Immediate Action**: The current IP is likely "hot". Switching networks (e.g., toggling Airplane mode on mobile hotspot, or connecting to a VPN) is the fastest way to reset the counter.
*   **Cookies**: Continue using `--cookies` to validate "legitimacy" of the requests, though this doesn't strictly prevent rate limits.

### 3. Algorithm Update
*   **Batch Size**: 5 videos.
*   **Intra-Batch Sleep**: 3-6 seconds.
*   **Inter-Batch Sleep**: 60 seconds.
*   **Est. Total Time**: 
    *   150 videos / 5 per batch = 30 batches.
    *   30 batches * 60s cooldown = 30 mins.
    *   Processing time = ~10 mins.
    *   **Total**: ~40 minutes. (Much better than 1.5 hours).

## Usage
```bash
# Run with Burst Mode (default settings optimization)
.venv/bin/python3 fetch_transcripts.py --csv data/04_enriched.csv --cookies cookies.txt --burst-mode
```
