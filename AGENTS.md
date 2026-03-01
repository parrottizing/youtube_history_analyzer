# Contributor Guide

## Project Structure

This repository is a step-based Python pipeline for analyzing YouTube watch history.

- `main.py`: orchestrates all pipeline stages in order.
- `steps/01_scrape_history.py` to `steps/06_visualize.py`: core workflow.
- `utils/`: shared helpers (`env_loader.py`, `date_utils.py`).
- `data/`: intermediate CSV artifacts from each stage.
- `output/`: final chart PNGs.
- `README.md`: user-facing setup and workflow documentation.

Legacy one-off scripts and Docker workflow were removed. Keep new work aligned with the current `steps/` pipeline.

## Pipeline Contracts

1. `steps/01_scrape_history.py`
- Scrapes `https://www.youtube.com/feed/history` using Selenium + Chrome profile in `chrome_data/`.
- Parses section headers into dates and targets the previous month range by default.
- Supports both old and newer YouTube history title selectors.
- Writes `data/01_raw_history.csv` with `Date,Title,Link`.

2. `steps/02_extract_ids.py`
- Extracts `VideoID` from `watch`, `shorts`, and `youtu.be` URL formats.
- Writes `data/02_video_ids.csv`.

3. `steps/03_deduplicate.py`
- Deduplicates by `VideoID`, keeping first occurrence.
- Writes `data/03_unique_ids.csv`.

4. `steps/04_enrich_metadata.py`
- Calls YouTube Data API (`videos` endpoint; `snippet,contentDetails`) in batches of 50.
- Requires `YOU_TUBE_API_KEY`.
- Writes `data/04_enriched.csv` with channel/title/duration/language/description/tags fields.

5. `steps/05_video_categorizer.py`
- Uses Groq chat completions for single-label classification.
- Requires `GROQ_API_KEY`.
- Optional `GROQ_MODEL` override (default `moonshotai/kimi-k2-instruct`).
- Writes `data/05_categorized.csv`.

6. `steps/06_visualize.py`
- Generates six charts under `output/` from `data/05_categorized.csv`.

## Environment and Dependencies

Use Python 3.10+ in a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install selenium webdriver-manager
```

Required `.env` keys:

```env
YOU_TUBE_API_KEY=...
GROQ_API_KEY=...
```

## Build and Run Commands

Run full pipeline:

```bash
python main.py
```

Run an individual stage:

```bash
python steps/04_enrich_metadata.py
```

Quick syntax check before opening a PR:

```bash
python -m py_compile main.py steps/*.py utils/*.py
```

## Coding Style

- Follow PEP 8 with 4-space indentation and `snake_case` names.
- Keep scripts focused and deterministic where possible.
- Prefer explicit input validation and fail-fast checks for missing files/keys.
- Keep file paths relative to repository root (`data/...`, `output/...`).

## Testing and Validation

There is no formal automated suite yet. Validate with:

- Full pipeline smoke run (`python main.py`).
- Stage-level reruns for edited files.
- Output checks:
  - `data/01_raw_history.csv` ... `data/05_categorized.csv`
  - six PNGs in `output/`

For non-trivial pure logic additions (parsing/normalization), add lightweight tests in `tests/`.

## External API/Library Changes

When implementing new features that depend on external libraries or APIs, verify against current documentation first (Context7).

## PR and Commit Guidelines

- Use focused commits with imperative messages (for example, `fix: handle missing video duration`).
- Keep PRs scoped to one behavior change; avoid mixing refactors with features.
- In PR descriptions, include:
  - what changed
  - why it changed
  - validation commands run
  - sample output paths
- Never commit secrets (`.env`, API keys) or generated artifacts (`*.csv`, `*.png`, browser profile data).

