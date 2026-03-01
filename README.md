# YouTube History Analyzer

Python pipeline for scraping, enriching, categorizing, and visualizing YouTube watch history.

This repository now uses the step-based workflow in `main.py` + `steps/`.
Legacy scripts and Docker workflow were removed.

## Pipeline Overview

```mermaid
flowchart LR
    A[Step 1: Scrape History] --> B[Step 2: Extract Video IDs]
    B --> C[Step 3: Deduplicate]
    C --> D[Step 4: Enrich Metadata]
    D --> E[Step 5: Categorize Videos]
    E --> F[Step 6: Visualize]
```

## Repository Structure

- `main.py`: runs all six steps in order.
- `steps/01_scrape_history.py`: Selenium scraper for YouTube history page.
- `steps/02_extract_ids.py`: extracts `VideoID` from YouTube URLs.
- `steps/03_deduplicate.py`: keeps latest row per `VideoID`.
- `steps/04_enrich_metadata.py`: YouTube Data API metadata enrichment.
- `steps/05_video_categorizer.py`: Groq-based category labeling.
- `steps/06_visualize.py`: generates charts from categorized CSV.
- `utils/date_utils.py`: date parsing and last-month range helpers.
- `utils/env_loader.py`: loads `.env` variables.
- `data/`: intermediate CSV outputs.
- `output/`: final PNG charts.

## Requirements

- Python 3.10+
- Google Chrome installed locally
- A signed-in YouTube account (used by Step 1 browser session)
- API keys:
  - YouTube Data API v3 key
  - Groq API key

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install selenium webdriver-manager
```

## Environment Variables

Create a `.env` file in the project root:

```env
YOU_TUBE_API_KEY=your_youtube_data_api_key
GROQ_API_KEY=your_groq_api_key
# Optional override (default shown):
GROQ_MODEL=moonshotai/kimi-k2-instruct
```

## Run

Run the full pipeline:

```bash
python main.py
```

Run individual steps:

```bash
python steps/01_scrape_history.py
python steps/02_extract_ids.py
python steps/03_deduplicate.py
python steps/04_enrich_metadata.py
python steps/05_video_categorizer.py
python steps/06_visualize.py
```

## Step Outputs

1. `steps/01_scrape_history.py`
- Input: YouTube history page (`https://www.youtube.com/feed/history`)
- Output: `data/01_raw_history.csv`
- Notes:
  - Targets the previous calendar month by default (`utils/date_utils.py`).
  - Applies the `Videos` chip to reduce Shorts.
  - Supports both old and newer YouTube history title selectors.

2. `steps/02_extract_ids.py`
- Input: `data/01_raw_history.csv`
- Output: `data/02_video_ids.csv`
- Notes:
  - Handles `watch?v=`, `/shorts/`, and `youtu.be` URL formats.

3. `steps/03_deduplicate.py`
- Input: `data/02_video_ids.csv`
- Output: `data/03_unique_ids.csv`
- Notes:
  - Deduplicates by `VideoID`, keeping first (most recent) occurrence.

4. `steps/04_enrich_metadata.py`
- Input: `data/03_unique_ids.csv`
- Output: `data/04_enriched.csv`
- Notes:
  - Fetches `snippet` + `contentDetails` from YouTube Data API in batches of 50.
  - Adds/updates `Channel`, `Duration`, `OriginalLanguage`, `Title`, `Description`, `Tags`.

5. `steps/05_video_categorizer.py`
- Input: `data/04_enriched.csv`
- Output: `data/05_categorized.csv`
- Notes:
  - Uses Groq chat completion with deterministic settings (`temperature=0`).
  - Categories:
    - `AI and coding`
    - `F1`
    - `Football`
    - `Basketball`
    - `News`
    - `Humor`
    - `Popular Science`
    - `History`
    - `Superheroes`
    - `Other`

6. `steps/06_visualize.py`
- Input: `data/05_categorized.csv`
- Output: `output/*.png`
- Generated charts:
  - `top_channels_by_count.png`
  - `top_channels_by_time.png`
  - `language_distribution.png`
  - `watch_time_by_language.png`
  - `categories_by_video_count.png`
  - `categories_by_watch_time.png`

## Validation

Quick syntax check:

```bash
python -m py_compile main.py steps/*.py utils/*.py
```

Smoke test:

```bash
python main.py
```

Verify expected artifacts:

- CSV chain exists in `data/` (`01_...` through `05_...`)
- Six PNG charts exist in `output/`

## Troubleshooting

- Step 1 cannot find `Videos` chip:
  - YouTube UI localization/layout can change selectors.
  - Confirm you are on `https://www.youtube.com/feed/history` and logged in.
- Step 4 fails with API error:
  - Check `YOU_TUBE_API_KEY` in `.env` and API quota.
- Step 5 fails with auth/rate-limit:
  - Check `GROQ_API_KEY` and retry.
- Empty output CSVs:
  - Ensure history page has viewable entries for the targeted month.

## Privacy and Git Hygiene

Do not commit:

- `.env` or API keys
- generated `data/*.csv`
- generated `output/*.png`
- browser profile/session data in `chrome_data/`

