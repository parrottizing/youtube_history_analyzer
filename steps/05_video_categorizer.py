import csv
import os
import sys
import time
import re

from groq import Groq

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.env_loader import load_env
except ImportError:
    from utils.env_loader import load_env

VALID_CATEGORIES = [
    "AI and coding",
    "F1",
    "Football",
    "Basketball",
    "News",
    "Humor",
    "Popular Science",
    "History",
    "Superheroes",
    "Other",
]

VALID_CATEGORY_MAP = {c.lower(): c for c in VALID_CATEGORIES}


def print_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()


def clean_text(value):
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def setup_groq_client():
    load_env()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env")
    return Groq(api_key=api_key)


def build_prompt(title, description, tags):
    title = title or "Unknown"
    description = description or "None"
    tags = tags or "None"

    prompt = f"""Analyze this YouTube video using its metadata.

Title: {title}

Description:
{description}

Tags:
{tags}

Based on the title, description, and tags, categorize this video into ONE of these categories ONLY:
AI and coding, F1, Football, Basketball, News, Humor, Popular Science, History, Superheroes, Other

Answer with only ONE category from the list above. No explanation, no additional text.

Category:"""
    return prompt


def normalize_category(text):
    if not text:
        return None

    # Take the first line and trim whitespace/quotes.
    cleaned = text.strip().splitlines()[0].strip()
    cleaned = cleaned.strip('"').strip("'")
    cleaned = re.sub(r'^\s*category\s*[:\-]\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip(" .,:;!#")

    lowered = cleaned.lower()
    if lowered in VALID_CATEGORY_MAP:
        return VALID_CATEGORY_MAP[lowered]

    # Fallback: try to find any category name inside the response.
    for cat in VALID_CATEGORIES:
        if cat.lower() in lowered:
            return cat

    return None


def categorize_video(client, title, description, tags, max_attempts=5):
    prompt = build_prompt(title, description, tags)
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        try:
            completion = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "moonshotai/kimi-k2-instruct"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=10,
                top_p=0.95,
            )
            raw = (completion.choices[0].message.content or "").strip()
            category = normalize_category(raw)
            if category:
                return category

            print_flush(
                f"Warning: Unexpected category response '{raw}'. Retrying ({attempt}/{max_attempts})..."
            )
            time.sleep(1.5)
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "rate limit" in err:
                wait_time = min(60 * (1.5 ** (attempt - 1)), 120)
                print_flush(
                    f"Rate limit error. Waiting {wait_time:.1f}s (attempt {attempt}/{max_attempts})..."
                )
                time.sleep(wait_time)
            else:
                print_flush(
                    f"Groq error: {e}. Retrying ({attempt}/{max_attempts})..."
                )
                time.sleep(3)

    return "Other"


def main():
    print("Starting Video Categorization (Step 5)...")

    input_file = os.path.join("data", "04_enriched.csv")
    output_file = os.path.join("data", "05_categorized.csv")

    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Run step 4 first.")
        return

    try:
        client = setup_groq_client()
    except Exception as e:
        print(f"Error setting up Groq client: {e}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if not rows:
        print("No rows found to categorize.")
        return

    desired_order = [
        "Date",
        "Title",
        "Channel",
        "Duration",
        "OriginalLanguage",
        "Category",
        "VideoID",
        "Link",
        "Description",
        "Tags",
    ]

    if "Category" not in fieldnames:
        fieldnames = fieldnames + ["Category"]

    # Enforce desired column order, while preserving any unexpected fields at the end
    extra_fields = [f for f in fieldnames if f not in desired_order]
    fieldnames = [f for f in desired_order if f in fieldnames] + extra_fields

    total = len(rows)
    print_flush(f"Categorizing {total} videos...")

    categorized_rows = []
    for idx, row in enumerate(rows, start=1):
        channel = clean_text(row.get("Channel", ""))
        title = clean_text(row.get("Title", ""))
        description = clean_text(row.get("Description", ""))
        tags = clean_text(row.get("Tags", ""))

        category = categorize_video(client, title, description, tags)
        row["Category"] = category

        categorized_rows.append(row)
        display_channel = channel if channel else "Unknown Channel"
        display_title = title if title else "Untitled"
        print_flush(
            f"[{idx}/{total}] {display_channel} | {display_title[:60]} -> {category}"
        )

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(categorized_rows)

    print(f"Categorized data saved to {output_file}")


if __name__ == "__main__":
    main()
