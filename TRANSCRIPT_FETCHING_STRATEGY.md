# YouTube Transcript Fetching Strategy

## Objective
Fetch transcripts for ~150 YouTube videos quickly, reliably, and without polluting the user's watch history.

## Status Update (2026-02-02) - CRITICAL FINDINGS
The initial "Hybrid Approach" encountered significant **Rate Limiting (HTTP 429)**.

### Diagnosis of Failure
1.  **Translation Trigger**: Attempting to translate transcripts via the API (e.g., Russian -> English) appears to be a high-risk activity that triggers YouTube's bot detection almost immediately.
2.  **IP Reputation**: Once the IP is flagged by the API, fallback requests via `yt-dlp` (even with cookies) also start failing with 429 errors.
3.  **Aggressive Timing**: The previous delay (2-5 seconds) was too short for a flagged IP.

## Revised Strategy: "Safe Mode"

To bypass these blocks, we must pivot from "Maximum Speed" to "Maximum Stealth".

### 1. Disable API Translation
*   **Why**: The translation endpoint seems to have stricter rate limits.
*   **New Logic**: Fetch the **original language** transcript only. Do not attempt to translate it during the download phase. We can translate it locally later using an LLM or other tool, which is safer.

### 2. Increase Delays Significantly
*   **Standard Sleep**: Increase from ~3s to **20-40 seconds**.
*   **Cooldown**: If a 429 is hit, sleep for **5 minutes** (not just 10s).

### 3. Processing Order
*   Process the list slowly in the background. ~150 videos * 30s = ~75 minutes. This is slower but reliable.

### 4. Alternative Backup: Anonymous Browser
*   If the Python API remains blocked, the next step is **Selenium/Playwright in Incognito Mode**.
    *   **Pros**: Emulates a real user (executes JS), bypasses API limits.
    *   **Privacy**: Incognito mode ensures NO watch history pollution.
    *   **Cons**: Requires browser overhead, slower.

## Implementation Plan (Step-by-Step)
1.    .venv/bin/python3 fetch_transcripts.py --csv data/04_enriched.csv --cookies cookies.txt --safe` flag.
    *   Remove translation attempts (fetch only `en` or `original`).
    *   Increase default sleep to 30s.
    *   Implement "Cool Down" blocks (sleep 300s on 429).

2.  **User Action**:
    *   Stop current script.
    *   Wait ~30 mins for IP block to expire.
    *   Run with `--safe` flag.
