import os
import re
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Fix Unicode encoding for Windows console (just in case)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def parse_duration_seconds(duration_str):
    if not isinstance(duration_str, str):
        return 0

    value = duration_str.strip()
    if not value:
        return 0

    # ISO 8601 like PT1H2M10S
    if value.startswith("PT"):
        pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
        match = pattern.fullmatch(value)
        if not match:
            return 0
        hours, minutes, seconds = match.groups()
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0
        return hours * 3600 + minutes * 60 + seconds

    # HH:MM:SS or MM:SS
    if ":" in value:
        parts = value.split(":")
        try:
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return 0

    return 0


def format_time_display(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def map_language(lang):
    if not isinstance(lang, str) or not lang.strip():
        return "Other"
    value = lang.strip().lower()
    if re.match(r"^ru($|[-_])", value) or "russian" in value or value == "rus":
        return "Russian"
    if re.match(r"^en($|[-_])", value) or "english" in value or "british" in value or value == "eng":
        return "English"
    return "Other"


def pick_languages(columns):
    ordered = ["Russian", "English", "Other"]
    return [lang for lang in ordered if lang in columns]


def annotate_stacked(ax, x_values, stacks, bottoms, formatter, min_display=0):
    for idx, (height, bottom) in enumerate(zip(stacks, bottoms)):
        if height <= min_display:
            continue
        ax.text(
            x_values[idx],
            bottom + height / 2,
            formatter(height),
            ha="center",
            va="center",
            fontweight="bold",
            color="white",
            fontsize=9,
        )


def annotate_stacked_time(ax, x_values, values_seconds, bottoms_hours, min_display_hours=0):
    for idx, seconds in enumerate(values_seconds):
        height_hours = seconds / 3600
        if height_hours <= min_display_hours:
            continue
        ax.text(
            x_values[idx],
            bottoms_hours[idx] + height_hours / 2,
            format_time_display(seconds),
            ha="center",
            va="center",
            fontweight="bold",
            color="white",
            fontsize=9,
        )


def main():
    print("Starting Visualization (Step 6)...")

    input_file = os.path.join("data", "05_categorized.csv")
    output_dir = "output"

    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Run previous steps.")
        return

    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} records.")

    df["DurationSeconds"] = df["Duration"].apply(parse_duration_seconds)
    df["LangGroup"] = df["OriginalLanguage"].apply(map_language)
    df["Category"] = df["Category"].fillna("Unknown")

    plt.style.use("default")
    plt.rcParams["font.family"] = ["DejaVu Sans", "Arial", "sans-serif"]
    plt.rcParams["axes.grid"] = True
    plt.rcParams["grid.alpha"] = 0.3

    language_colors = {
        "Russian": "#FF6B6B",
        "English": "#4ECDC4",
        "Other": "#95A5A6",
    }

    # === Graph 1: Top Channels by Count (Language Breakdown) ===
    try:
        channel_lang_counts = df.groupby(["Channel", "LangGroup"]).size().unstack(fill_value=0)
        channel_totals = channel_lang_counts.sum(axis=1).sort_values(ascending=False)
        top_channels = channel_totals.head(10).index
        data = channel_lang_counts.loc[top_channels]
        languages = pick_languages(data.columns)

        x = np.arange(len(top_channels))
        width = 0.6
        bottom = np.zeros(len(top_channels))

        plt.figure(figsize=(14, 8))
        for lang in languages:
            values = data[lang].values
            bars = plt.bar(x, values, width, bottom=bottom, label=lang, color=language_colors[lang], alpha=0.85)
            annotate_stacked(plt.gca(), x, values, bottom, lambda v: f"{int(v)}", min_display=999999)
            bottom = bottom + values

        for idx, total in enumerate(channel_totals.loc[top_channels]):
            plt.text(idx, total + 0.05, f"{int(total)}", ha="center", va="bottom", fontweight="bold", fontsize=10)

        max_total = channel_totals.loc[top_channels].max()
        plt.ylim(0, max_total * 1.05)

        plt.title("Top 10 Channels by Video Count", fontsize=16, fontweight="bold", pad=20)
        plt.xlabel("Channel", fontsize=12, fontweight="bold")
        plt.ylabel("Videos Watched", fontsize=12, fontweight="bold")
        plt.xticks(x, [name if len(name) <= 24 else name[:21] + "..." for name in top_channels], rotation=45, ha="right")
        plt.legend(fontsize=10)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "top_channels_by_count.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print("Saved top_channels_by_count.png")
    except Exception as exc:
        print(f"Error generating channel count graph: {exc}")

    # === Graph 2: Top Channels by Watch Time (Language Breakdown) ===
    try:
        channel_lang_time = df.groupby(["Channel", "LangGroup"])["DurationSeconds"].sum().unstack(fill_value=0)
        channel_time_totals = channel_lang_time.sum(axis=1).sort_values(ascending=False)
        top_time_channels = channel_time_totals.head(10).index
        data = channel_lang_time.loc[top_time_channels]
        languages = pick_languages(data.columns)

        x = np.arange(len(top_time_channels))
        width = 0.6
        bottom = np.zeros(len(top_time_channels))

        plt.figure(figsize=(14, 8))
        for lang in languages:
            values_seconds = data[lang].values
            values_hours = values_seconds / 3600
            plt.bar(x, values_hours, width, bottom=bottom, label=lang, color=language_colors[lang], alpha=0.85)
            annotate_stacked_time(plt.gca(), x, values_seconds, bottom, min_display_hours=9999)
            bottom = bottom + values_hours

        for idx, total_seconds in enumerate(channel_time_totals.loc[top_time_channels]):
            plt.text(idx, (total_seconds / 3600) + 0.05, format_time_display(total_seconds), ha="center", va="bottom", fontweight="bold", fontsize=10)

        max_total_hours = (channel_time_totals.loc[top_time_channels] / 3600).max()
        plt.ylim(0, max_total_hours * 1.15)

        plt.title("Top 10 Channels by Watch Time", fontsize=16, fontweight="bold", pad=20)
        plt.xlabel("Channel", fontsize=12, fontweight="bold")
        plt.ylabel("Watch Time (Hours)", fontsize=12, fontweight="bold")
        plt.xticks(x, [name if len(name) <= 24 else name[:21] + "..." for name in top_time_channels], rotation=45, ha="right")
        plt.legend(fontsize=10)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "top_channels_by_time.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print("Saved top_channels_by_time.png")
    except Exception as exc:
        print(f"Error generating channel time graph: {exc}")

    # === Graph 3: Language Distribution by Count ===
    try:
        language_counts = df["LangGroup"].value_counts()
        languages = pick_languages(language_counts.index)
        values = [language_counts[lang] for lang in languages]
        colors = [language_colors[lang] for lang in languages]

        plt.figure(figsize=(8, 8))
        wedges, texts, autotexts = plt.pie(
            values,
            labels=languages,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
            explode=[0.05] * len(languages),
            shadow=True,
        )
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
        total_videos = int(sum(values))
        stats_lines = [f"Total videos: {total_videos}"]
        for lang in languages:
            stats_lines.append(f"{lang}: {int(language_counts[lang])}")
        plt.text(
            1.2,
            0.5,
            "\n".join(stats_lines),
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8),
        )
        plt.title("Language Distribution (Video Count)", fontsize=15, fontweight="bold", pad=20)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "language_distribution.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print("Saved language_distribution.png")
    except Exception as exc:
        print(f"Error generating language distribution graph: {exc}")

    # === Graph 4: Watch Time by Language ===
    try:
        time_by_language = df.groupby("LangGroup")["DurationSeconds"].sum()
        languages = pick_languages(time_by_language.index)
        values = [time_by_language[lang] for lang in languages]
        colors = [language_colors[lang] for lang in languages]

        plt.figure(figsize=(8, 8))
        wedges, texts, autotexts = plt.pie(
            values,
            labels=languages,
            colors=colors,
            autopct=lambda pct: "{:.1f}%".format(pct) if pct > 0 else "",
            startangle=90,
            explode=[0.05] * len(languages),
            shadow=True,
        )
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
        total_seconds = sum(values)
        stats_lines = [f"Total time: {format_time_display(total_seconds)}"]
        for lang in languages:
            stats_lines.append(f"{lang}: {format_time_display(time_by_language[lang])}")
        plt.text(
            1.2,
            0.5,
            "\n".join(stats_lines),
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8),
        )
        plt.title("Watch Time by Language", fontsize=15, fontweight="bold", pad=20)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "watch_time_by_language.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print("Saved watch_time_by_language.png")
    except Exception as exc:
        print(f"Error generating watch time by language graph: {exc}")

    # === Graph 5: Top Categories by Count (Language Breakdown) ===
    try:
        category_lang_counts = df.groupby(["Category", "LangGroup"]).size().unstack(fill_value=0)
        category_totals = category_lang_counts.sum(axis=1).sort_values(ascending=False)
        top_categories = category_totals.head(8).index
        data = category_lang_counts.loc[top_categories]
        languages = pick_languages(data.columns)

        x = np.arange(len(top_categories))
        width = 0.6
        bottom = np.zeros(len(top_categories))

        plt.figure(figsize=(14, 8))
        for lang in languages:
            values = data[lang].values
            bars = plt.bar(x, values, width, bottom=bottom, label=lang, color=language_colors[lang], alpha=0.85)
            annotate_stacked(plt.gca(), x, values, bottom, lambda v: f"{int(v)}", min_display=0)
            bottom = bottom + values

        for idx, total in enumerate(category_totals.loc[top_categories]):
            plt.text(idx, total + 0.3, f"{int(total)}", ha="center", va="bottom", fontweight="bold", fontsize=10)

        plt.title("Top Categories by Video Count", fontsize=16, fontweight="bold", pad=20)
        plt.xlabel("Category", fontsize=12, fontweight="bold")
        plt.ylabel("Videos Watched", fontsize=12, fontweight="bold")
        plt.xticks(x, [name if len(name) <= 24 else name[:21] + "..." for name in top_categories], rotation=45, ha="right")
        plt.legend(fontsize=10)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "categories_by_video_count.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print("Saved categories_by_video_count.png")
    except Exception as exc:
        print(f"Error generating category count graph: {exc}")

    # === Graph 6: Top Categories by Watch Time (Language Breakdown) ===
    try:
        category_lang_time = df.groupby(["Category", "LangGroup"])["DurationSeconds"].sum().unstack(fill_value=0)
        category_time_totals = category_lang_time.sum(axis=1).sort_values(ascending=False)
        top_time_categories = category_time_totals.head(8).index
        data = category_lang_time.loc[top_time_categories]
        languages = pick_languages(data.columns)

        x = np.arange(len(top_time_categories))
        width = 0.6
        bottom = np.zeros(len(top_time_categories))

        plt.figure(figsize=(14, 8))
        for lang in languages:
            values_seconds = data[lang].values
            values_hours = values_seconds / 3600
            plt.bar(x, values_hours, width, bottom=bottom, label=lang, color=language_colors[lang], alpha=0.85)
            annotate_stacked_time(plt.gca(), x, values_seconds, bottom, min_display_hours=0.1)
            bottom = bottom + values_hours

        for idx, total_seconds in enumerate(category_time_totals.loc[top_time_categories]):
            plt.text(idx, (total_seconds / 3600) + 0.05, format_time_display(total_seconds), ha="center", va="bottom", fontweight="bold", fontsize=10)

        max_total_hours = (category_time_totals.loc[top_time_categories] / 3600).max()
        plt.ylim(0, max_total_hours * 1.15)

        plt.title("Top Categories by Watch Time", fontsize=16, fontweight="bold", pad=20)
        plt.xlabel("Category", fontsize=12, fontweight="bold")
        plt.ylabel("Watch Time (Hours)", fontsize=12, fontweight="bold")
        plt.xticks(x, [name if len(name) <= 24 else name[:21] + "..." for name in top_time_categories], rotation=45, ha="right")
        plt.legend(fontsize=10)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "categories_by_watch_time.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print("Saved categories_by_watch_time.png")
    except Exception as exc:
        print(f"Error generating category time graph: {exc}")

    print(f"Graphs saved to {output_dir}/")


if __name__ == "__main__":
    main()
