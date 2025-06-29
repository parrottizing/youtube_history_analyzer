#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Настройка для поддержки русского языка
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']

def parse_duration_to_seconds(duration_str):
    """Парсит длительность видео в секунды"""
    try:
        if ':' in duration_str:
            parts = duration_str.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
        return 0
    except:
        return 0

def format_time_display(seconds):
    """Форматирует секунды в читаемый вид"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}ч {minutes}м"
    else:
        return f"{minutes}м"

def main():
    print("=== Создание графиков по категориям YouTube ===\n")
    
    # Читаем данные
    try:
        df = pd.read_csv('youtube_history_with_categories.csv')
        print(f"✅ Загружен файл с {len(df)} видео")
    except FileNotFoundError:
        print("❌ Файл 'youtube_history_with_categories.csv' не найден")
        return
    
    # Добавляем колонку с длительностью в секундах
    df['Duration_Seconds'] = df['Длительность видео'].apply(parse_duration_to_seconds)
    
    # === График 1: Топ категории по количеству видео ===
    plt.figure(figsize=(14, 8))
    
    # Группируем по категориям и языкам
    category_lang_counts = df.groupby(['Category', 'Language']).size().unstack(fill_value=0)
    category_totals = df['Category'].value_counts()
    top_categories = category_totals.head(8).index
    
    filtered_data = category_lang_counts.loc[top_categories]
    colors = {'Russian': '#FF6B6B', 'English': '#4ECDC4'}
    
    x = np.arange(len(top_categories))
    width = 0.6
    
    # Создаем стековые столбцы
    russian_counts = [filtered_data.loc[cat, 'Russian'] if 'Russian' in filtered_data.columns else 0 for cat in top_categories]
    english_counts = [filtered_data.loc[cat, 'English'] if 'English' in filtered_data.columns else 0 for cat in top_categories]
    
    bars1 = plt.bar(x, russian_counts, width, label='🇷🇺 Русский', color=colors['Russian'], alpha=0.8)
    bars2 = plt.bar(x, english_counts, width, bottom=russian_counts, label='🇺🇸 English', color=colors['English'], alpha=0.8)
    
    # Добавляем значения на столбцы
    for i, (rus, eng) in enumerate(zip(russian_counts, english_counts)):
        total = rus + eng
        if rus > 0:
            plt.text(i, rus/2, str(rus), ha='center', va='center', fontweight='bold', color='white')
        if eng > 0:
            plt.text(i, rus + eng/2, str(eng), ha='center', va='center', fontweight='bold', color='white')
        plt.text(i, total + 0.3, str(total), ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    plt.title('🏆 Топ категории по количеству видео', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Категории', fontsize=12, fontweight='bold')
    plt.ylabel('Количество видео', fontsize=12, fontweight='bold')
    plt.xticks(x, top_categories, rotation=45, ha='right')
    plt.legend(fontsize=11)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('categories_by_video_count.png', dpi=300, bbox_inches='tight')
    print("✅ График 'categories_by_video_count.png' создан")
    plt.close()
    
    # === График 2: Топ категории по времени просмотра ===
    plt.figure(figsize=(14, 8))
    
    category_lang_time = df.groupby(['Category', 'Language'])['Duration_Seconds'].sum().unstack(fill_value=0)
    category_time_totals = df.groupby('Category')['Duration_Seconds'].sum().sort_values(ascending=False)
    top_time_categories = category_time_totals.head(8).index
    
    filtered_time_data = category_lang_time.loc[top_time_categories]
    x = np.arange(len(top_time_categories))
    
    # Время в часах для отображения
    russian_time = [filtered_time_data.loc[cat, 'Russian']/3600 if 'Russian' in filtered_time_data.columns else 0 for cat in top_time_categories]
    english_time = [filtered_time_data.loc[cat, 'English']/3600 if 'English' in filtered_time_data.columns else 0 for cat in top_time_categories]
    
    bars1 = plt.bar(x, russian_time, width, label='🇷🇺 Русский', color=colors['Russian'], alpha=0.8)
    bars2 = plt.bar(x, english_time, width, bottom=russian_time, label='🇺🇸 English', color=colors['English'], alpha=0.8)
    
    # Добавляем значения на столбцы
    for i, (rus, eng) in enumerate(zip(russian_time, english_time)):
        total_seconds = category_time_totals[top_time_categories[i]]
        rus_seconds = filtered_time_data.loc[top_time_categories[i], 'Russian'] if 'Russian' in filtered_time_data.columns else 0
        eng_seconds = filtered_time_data.loc[top_time_categories[i], 'English'] if 'English' in filtered_time_data.columns else 0
        
        if rus > 0.1:
            plt.text(i, rus/2, format_time_display(rus_seconds), ha='center', va='center', 
                    fontweight='bold', color='white', fontsize=9)
        if eng > 0.1:
            plt.text(i, rus + eng/2, format_time_display(eng_seconds), ha='center', va='center', 
                    fontweight='bold', color='white', fontsize=9)
        
        total_time_str = format_time_display(total_seconds)
        plt.text(i, rus + eng + 0.1, total_time_str, ha='center', va='bottom', 
                fontweight='bold', fontsize=10)
    
    plt.title('⏱️ Топ категории по времени просмотра', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Категории', fontsize=12, fontweight='bold')
    plt.ylabel('Время просмотра (часы)', fontsize=12, fontweight='bold')
    plt.xticks(x, top_time_categories, rotation=45, ha='right')
    plt.legend(fontsize=11)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('categories_by_watch_time.png', dpi=300, bbox_inches='tight')
    print("✅ График 'categories_by_watch_time.png' создан")
    plt.close()
    
    # === Статистика ===
    print("\n📊 Статистика по категориям:")
    print("\n🎬 По количеству видео:")
    for category in top_categories:
        total = category_totals[category]
        rus_count = filtered_data.loc[category, 'Russian'] if 'Russian' in filtered_data.columns else 0
        eng_count = filtered_data.loc[category, 'English'] if 'English' in filtered_data.columns else 0
        print(f"   {category}: {total} видео (🇷🇺 {rus_count} | 🇺🇸 {eng_count})")
    
    print("\n⏱️ По времени просмотра:")
    for category in top_time_categories:
        total_time = category_time_totals[category]
        rus_time = filtered_time_data.loc[category, 'Russian'] if 'Russian' in filtered_time_data.columns else 0
        eng_time = filtered_time_data.loc[category, 'English'] if 'English' in filtered_time_data.columns else 0
        
        total_str = format_time_display(total_time)
        rus_str = format_time_display(rus_time)
        eng_str = format_time_display(eng_time)
        
        print(f"   {category}: {total_str} (🇷🇺 {rus_str} | 🇺🇸 {eng_str})")
    
    print(f"\n🎯 Графики категорий успешно созданы!")

if __name__ == "__main__":
    main() 