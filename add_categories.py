#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import os
import sys
import time
from collections import defaultdict

# Fix Unicode encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def setup_gemini():
    """Настройка Gemini API"""
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY не найден в .env файле")
    
    genai.configure(api_key=api_key)
    
    # Настройка модели
    generation_config = {
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 10,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
    )
    
    return model

def categorize_channel(model, channel_name, video_titles):
    """Категоризация канала с помощью Gemini AI - НИКОГДА не сдаемся!"""
    
    # Создаем промпт
    titles_text = "\n".join([f"- {title}" for title in video_titles])
    
    prompt = f"""Analyze this YouTube channel and its video titles. 

Channel Name: {channel_name}

Video Titles:
{titles_text}

Based on the channel name and video titles, categorize this channel into ONE of these categories ONLY:
AI, F1, Football, Basketball, News, Humor, Popular Science, History, Superheroes, Other

Answer with only ONE WORD from the list above. No explanation, no additional text.

Category:"""
    
    attempt = 0
    while True:  # НИКОГДА НЕ СДАЕМСЯ!
        attempt += 1
        try:
            response = model.generate_content(prompt)
            category = response.text.strip().upper()
            
            # Проверяем, что ответ в списке допустимых категорий
            valid_categories = ['AI', 'F1', 'FOOTBALL', 'BASKETBALL', 'NEWS', 'HUMOR', 'POPULAR SCIENCE', 'HISTORY', 'SUPERHEROES', 'OTHER']
            
            if category in valid_categories:
                if attempt > 1:
                    print(f"Успешно получили категорию после {attempt} попыток")
                return category
            else:
                print(f"Gemini вернул неожиданную категорию '{category}' для канала '{channel_name}'. Пробуем еще раз...")
                time.sleep(5)  # Небольшая пауза перед повтором
                continue
                
        except Exception as e:
            if "429" in str(e):
                # Экспоненциальный backoff для rate limits
                wait_time = min(60 * (1.5 ** (attempt - 1)), 300)  # Максимум 5 минут
                print(f"Rate limit error для канала '{channel_name}'. Ждем {wait_time:.1f} секунд... (попытка {attempt})")
                time.sleep(wait_time)
                continue
            elif "quota" in str(e).lower():
                # Достигнут дневной лимит - ждем дольше
                print(f"Достигнут дневной лимит API. Ждем 10 минут перед продолжением... (попытка {attempt})")
                time.sleep(600)  # 10 минут
                continue
            else:
                # Другие ошибки - короткая пауза и повтор
                print(f"Ошибка для канала '{channel_name}': {e}. Пробуем еще раз через 10 секунд... (попытка {attempt})")
                time.sleep(10)
                continue

def main():
    print("=== Добавление категорий к видео с помощью Gemini AI ===\n")
    
    # Настройка Gemini
    try:
        model = setup_gemini()
        print("Gemini API настроен успешно")
    except Exception as e:
        print(f"Ошибка настройки Gemini API: {e}")
        return
    
    # Читаем данные
    try:
        df = pd.read_csv('youtube_history_with_language.csv')
        print(f"Загружен файл с {len(df)} видео")
    except FileNotFoundError:
        print("Файл 'youtube_history_with_language.csv' не найден")
        return
    
    # Группируем по каналам
    channels_data = defaultdict(list)
    for _, row in df.iterrows():
        channel = row['Название канала']
        title = row['Название видео']
        channels_data[channel].append(title)
    
    print(f"Найдено {len(channels_data)} уникальных каналов")
    
    # Категоризуем каждый канал
    channel_categories = {}
    
    for i, (channel, titles) in enumerate(channels_data.items(), 1):
        # Безопасно выводим название канала, заменяя проблемные символы
        safe_channel_name = channel.encode('cp1251', 'replace').decode('cp1251')
        print(f"[{i}/{len(channels_data)}] Категоризуем канал: {safe_channel_name}")
        
        category = categorize_channel(model, channel, titles)
        channel_categories[channel] = category
        
        print(f"   Категория: {category}")
        
        # Соблюдаем лимит 15 RPM для Free Tier (4+ секунды между запросами)
        time.sleep(4.5)
    
    # Добавляем категории к основному DataFrame
    df['Category'] = df['Название канала'].map(channel_categories)
    
    # Сохраняем результат
    output_file = 'youtube_history_with_categories.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\nФайл с категориями сохранен: {output_file}")
    
    # Показываем статистику по категориям
    print("\nСтатистика по категориям:")
    category_stats = df['Category'].value_counts()
    for category, count in category_stats.items():
        print(f"   {category}: {count} видео")
    
    # Показываем каналы по категориям
    print("\nКаналы по категориям:")
    for category in sorted(category_stats.index):
        channels_in_category = df[df['Category'] == category]['Название канала'].unique()
        print(f"\n{category}:")
        for channel in sorted(channels_in_category):
            video_count = len(df[df['Название канала'] == channel])
            safe_channel = channel.encode('cp1251', 'replace').decode('cp1251')
            print(f"   - {safe_channel} ({video_count} видео)")

if __name__ == "__main__":
    main() 