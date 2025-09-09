#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys

# Fix Unicode encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def main():
    df = pd.read_csv('youtube_history_with_categories.csv')
    
    print("=== CATEGORY STATISTICS ===")
    category_stats = df['Category'].value_counts()
    for category, count in category_stats.items():
        print(f"{category}: {count} videos")
    
    print("\n=== CHANNELS BY CATEGORY ===")
    for category in sorted(df['Category'].unique()):
        print(f"\n{category}:")
        channels_in_category = df[df['Category'] == category]['Название канала'].value_counts()
        for channel, count in channels_in_category.items():
            print(f"   • {channel}: {count} videos")

if __name__ == "__main__":
    main() 