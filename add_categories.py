#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import os
import sys
import time
import json
from collections import defaultdict
from datetime import datetime

# Fix Unicode encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

class ChannelCategoryCache:
    """Manages cached channel-to-category mappings"""
    
    def __init__(self, cache_file='channel_categories.json'):
        self.cache_file = cache_file
        self.cache = {}
        self.new_categories = {}  # Track new categories discovered in this run
        self.load_cache()
    
    def load_cache(self):
        """Load existing cache from JSON file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"📚 Loaded {len(self.cache)} channel categories from cache")
            else:
                print(f"📚 No cache file found, starting fresh")
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
            self.cache = {}
    
    def get_category(self, channel_name):
        """Get category for a channel if it exists in cache"""
        return self.cache.get(channel_name)
    
    def add_category(self, channel_name, category):
        """Add a new category to cache"""
        self.cache[channel_name] = category
        self.new_categories[channel_name] = category
    
    def save_cache(self):
        """Save the updated cache to JSON file"""
        try:
            # Create backup of existing cache
            if os.path.exists(self.cache_file):
                backup_file = f"{self.cache_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                with open(self.cache_file, 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                print(f"🔒 Backup created: {backup_file}")
            
            # Save updated cache
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2, sort_keys=True)
            
            if self.new_categories:
                print(f"💾 Cache updated with {len(self.new_categories)} new categories")
                print("🆕 New categories discovered:")
                for channel, category in self.new_categories.items():
                    safe_channel_name = channel.encode('cp1251', 'replace').decode('cp1251')
                    print(f"   • {safe_channel_name} → {category}")
            else:
                print(f"💾 Cache saved (no new categories this run)")
                
        except Exception as e:
            print(f"❌ Error saving cache: {e}")

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
AI and coding, F1, Football, Basketball, News, Humor, Popular Science, History, Superheroes, Other

Answer with only ONE WORD from the list above. No explanation, no additional text.

Category:"""
    
    attempt = 0
    while True:  # НИКОГДА НЕ СДАЕМСЯ!
        attempt += 1
        try:
            response = model.generate_content(prompt)
            category = response.text.strip().upper()
            
            # Проверяем, что ответ в списке допустимых категорий
            valid_categories = ['AI AND CODING', 'F1', 'FOOTBALL', 'BASKETBALL', 'NEWS', 'HUMOR', 'POPULAR SCIENCE', 'HISTORY', 'SUPERHEROES', 'OTHER']
            
            if category in valid_categories:
                if attempt > 1:
                    print(f"✅ Успешно получили категорию после {attempt} попыток")
                return category
            else:
                print(f"⚠️ Gemini вернул неожиданную категорию '{category}' для канала '{channel_name}'. Пробуем еще раз...")
                time.sleep(5)  # Небольшая пауза перед повтором
                continue
                
        except Exception as e:
            if "429" in str(e):
                # Экспоненциальный backoff для rate limits
                wait_time = min(60 * (1.5 ** (attempt - 1)), 300)  # Максимум 5 минут
                print(f"⏳ Rate limit error для канала '{channel_name}'. Ждем {wait_time:.1f} секунд... (попытка {attempt})")
                time.sleep(wait_time)
                continue
            elif "quota" in str(e).lower():
                # Достигнут дневной лимит - ждем дольше
                print(f"⏳ Достигнут дневной лимит API. Ждем 10 минут перед продолжением... (попытка {attempt})")
                time.sleep(600)  # 10 минут
                continue
            else:
                # Другие ошибки - короткая пауза и повтор
                print(f"❌ Ошибка для канала '{channel_name}': {e}. Пробуем еще раз через 10 секунд... (попытка {attempt})")
                time.sleep(10)
                continue

def main():
    print("=== Добавление категорий к видео с помощью Gemini AI ===\n")
    
    # Инициализируем кэш
    cache = ChannelCategoryCache()
    
    # Настройка Gemini (только если нужно будет делать AI запросы)
    model = None
    
    # Читаем данные
    try:
        df = pd.read_csv('youtube_history_with_language.csv')
        print(f"📁 Загружен файл с {len(df)} видео")
    except FileNotFoundError:
        print("❌ Файл 'youtube_history_with_language.csv' не найден")
        return
    
    # Группируем по каналам
    channels_data = defaultdict(list)
    for _, row in df.iterrows():
        channel = row['Название канала']
        title = row['Название видео']
        channels_data[channel].append(title)
    
    print(f"🔍 Найдено {len(channels_data)} уникальных каналов")
    
    # Проверяем, сколько каналов уже в кэше
    cached_channels = 0
    unknown_channels = []
    
    for channel in channels_data.keys():
        if cache.get_category(channel):
            cached_channels += 1
        else:
            unknown_channels.append(channel)
    
    print(f"✅ В кэше уже есть {cached_channels} каналов")
    print(f"🤖 Нужно категоризовать {len(unknown_channels)} новых каналов с помощью AI")
    
    # Настраиваем Gemini только если есть новые каналы
    if unknown_channels:
        try:
            model = setup_gemini()
            print("🤖 Gemini API настроен успешно")
        except Exception as e:
            print(f"❌ Ошибка настройки Gemini API: {e}")
            return
    
    # Категоризуем каналы
    channel_categories = {}
    
    for i, (channel, titles) in enumerate(channels_data.items(), 1):
        safe_channel_name = channel.encode('cp1251', 'replace').decode('cp1251')
        
        # Сначала проверяем кэш
        cached_category = cache.get_category(channel)
        if cached_category:
            channel_categories[channel] = cached_category
            print(f"[{i}/{len(channels_data)}] 💾 {safe_channel_name} → {cached_category} (из кэша)")
        else:
            # Используем AI для новых каналов
            print(f"[{i}/{len(channels_data)}] 🤖 Категоризуем новый канал: {safe_channel_name}")
            
            if not model:
                print("❌ Gemini API не настроен для новых каналов")
                return
                
            category = categorize_channel(model, channel, titles)
            channel_categories[channel] = category
            cache.add_category(channel, category)
            
            print(f"   ✅ Категория: {category}")
            
            # Соблюдаем лимит 15 RPM для Free Tier (4+ секунды между запросами)
            time.sleep(4.5)
    
    # Сохраняем обновленный кэш
    cache.save_cache()
    
    # Добавляем категории к основному DataFrame
    df['Category'] = df['Название канала'].map(channel_categories)
    
    # Сохраняем результат
    timestamp = datetime.now().strftime('%H-%M-%S-%f')[:-3]
    output_file = f'output/youtube_history_with_categories.csv {timestamp}.csv'
    
    # Создаем папку output если не существует
    os.makedirs('output', exist_ok=True)
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n📊 Файл с категориями сохранен: {output_file}")
    
    # Показываем статистику по категориям
    print("\n📈 Статистика по категориям:")
    category_stats = df['Category'].value_counts()
    for category, count in category_stats.items():
        print(f"   {category}: {count} видео")
    
    # Показываем статистику по использованию кэша
    print(f"\n🎯 Эффективность кэширования:")
    print(f"   Использовано из кэша: {cached_channels} каналов")
    print(f"   Новых AI запросов: {len(unknown_channels)} каналов")
    if len(channels_data) > 0:
        cache_hit_rate = (cached_channels / len(channels_data)) * 100
        print(f"   Процент попаданий в кэш: {cache_hit_rate:.1f}%")
    
    print(f"\n🎉 Готово! Всего обработано {len(channels_data)} каналов")

if __name__ == "__main__":
    main()