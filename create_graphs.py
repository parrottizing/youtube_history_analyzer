import csv
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict
import re

# Set up matplotlib for better looking plots
plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

def parse_duration_seconds(duration_str):
    """
    Парсит строку длительности и возвращает секунды.
    """
    try:
        if ':' not in duration_str:
            return 0
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

def create_youtube_graphs():
    """
    Создает графики для анализа YouTube каналов.
    """
    print("Создаю графики для анализа YouTube каналов...")
    
    try:
        # Читаем данные о каналах
        df = pd.read_csv('channel_analysis.csv', encoding='utf-8-sig')
        video_df = pd.read_csv('youtube_history_with_language.csv', encoding='utf-8-sig')
        
        # График 1: Топ каналов по количеству видео
        plt.figure(figsize=(14, 8))
        
        top_channels = df.head(10)
        
        # Цвета для русских и английских каналов
        colors = ['#FF6B6B' if 'Russian' in lang else '#4ECDC4' 
                 for lang in top_channels['Языки']]
        
        bars = plt.bar(range(len(top_channels)), 
                      top_channels['Количество видео'],
                      color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        plt.title('🏆 Топ 10 каналов по количеству просмотренных видео', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Каналы', fontsize=12, fontweight='bold')
        plt.ylabel('Количество видео', fontsize=12, fontweight='bold')
        
        # Поворачиваем названия каналов
        channel_names = [name[:20] + '...' if len(name) > 20 else name 
                        for name in top_channels['Канал']]
        plt.xticks(range(len(top_channels)), channel_names, 
                  rotation=45, ha='right')
        
        # Добавляем значения на столбцы
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        # Легенда
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='#FF6B6B', label='🇷🇺 Русские каналы'),
                          Patch(facecolor='#4ECDC4', label='🇺🇸 Английские каналы')]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig('top_channels_by_count.png', dpi=300, bbox_inches='tight')
        print("✅ График 'top_channels_by_count.png' создан")
        plt.close()
        
        # График 2: Топ каналов по времени просмотра
        plt.figure(figsize=(14, 8))
        
        # Сортируем по времени
        df_by_time = df.sort_values('Общее время (секунды)', ascending=False)
        top_time = df_by_time.head(10)
        
        # Конвертируем в часы
        watch_time_hours = top_time['Общее время (секунды)'] / 3600
        
        colors_time = ['#FF6B6B' if 'Russian' in lang else '#4ECDC4' 
                      for lang in top_time['Языки']]
        
        bars2 = plt.bar(range(len(top_time)), 
                       watch_time_hours,
                       color=colors_time, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        plt.title('⏰ Топ 10 каналов по времени просмотра', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Каналы', fontsize=12, fontweight='bold')
        plt.ylabel('Время просмотра (часы)', fontsize=12, fontweight='bold')
        
        channel_names_time = [name[:20] + '...' if len(name) > 20 else name 
                             for name in top_time['Канал']]
        plt.xticks(range(len(top_time)), channel_names_time, 
                  rotation=45, ha='right')
        
        # Добавляем значения (часы:минуты)
        for i, bar in enumerate(bars2):
            height = bar.get_height()
            total_seconds = top_time.iloc[i]['Общее время (секунды)']
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            time_label = f"{hours}:{minutes:02d}"
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    time_label, ha='center', va='bottom', fontweight='bold')
        
        plt.legend(handles=legend_elements, loc='upper right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig('top_channels_by_time.png', dpi=300, bbox_inches='tight')
        print("✅ График 'top_channels_by_time.png' создан")
        plt.close()
        
        # График 3: Распределение по языкам
        plt.figure(figsize=(10, 8))
        
        language_counts = video_df['Language'].value_counts()
        
        colors_pie = ['#FF6B6B', '#4ECDC4']
        labels = ['🇷🇺 Русский', '🇺🇸 English']
        
        wedges, texts, autotexts = plt.pie(language_counts.values, 
                                          labels=labels,
                                          colors=colors_pie,
                                          autopct='%1.1f%%',
                                          startangle=90,
                                          explode=(0.05, 0.05),
                                          shadow=True)
        
        # Улучшаем текст
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(12)
        
        for text in texts:
            text.set_fontsize(12)
            text.set_fontweight('bold')
        
        plt.title('🌐 Распределение видео по языкам', 
                 fontsize=16, fontweight='bold', pad=20)
        
        # Статистика
        total_videos = len(video_df)
        russian_count = language_counts.get('Russian', 0)
        english_count = language_counts.get('English', 0)
        
        stats_text = f"Всего видео: {total_videos}\n🇷🇺 Русский: {russian_count}\n🇺🇸 English: {english_count}"
        plt.text(1.3, 0.5, stats_text, fontsize=11, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('language_distribution.png', dpi=300, bbox_inches='tight')
        print("✅ График 'language_distribution.png' создан")
        plt.close()
        
        # График 4: Распределение времени просмотра по языкам
        plt.figure(figsize=(10, 8))
        
        # Вычисляем общее время просмотра по языкам
        total_time_by_language = {'Russian': 0, 'English': 0}
        
        for _, row in video_df.iterrows():
            language = row['Language']
            duration_str = row['Длительность видео']
            
            # Парсим длительность в секунды
            try:
                if ':' in duration_str:
                    parts = duration_str.split(':')
                    if len(parts) == 2:  # MM:SS
                        minutes, seconds = map(int, parts)
                        total_seconds = minutes * 60 + seconds
                    elif len(parts) == 3:  # HH:MM:SS
                        hours, minutes, seconds = map(int, parts)
                        total_seconds = hours * 3600 + minutes * 60 + seconds
                    else:
                        total_seconds = 0
                else:
                    total_seconds = 0
            except:
                total_seconds = 0
            
            total_time_by_language[language] += total_seconds
        
        # Конвертируем в часы для отображения
        russian_hours = total_time_by_language['Russian'] / 3600
        english_hours = total_time_by_language['English'] / 3600
        total_hours = russian_hours + english_hours
        
        # Создаем данные для pie chart
        time_values = [total_time_by_language['Russian'], total_time_by_language['English']]
        time_labels = ['🇷🇺 Русский', '🇺🇸 English']
        time_colors = ['#FF6B6B', '#4ECDC4']
        
        # Вычисляем проценты
        russian_percent = (total_time_by_language['Russian'] / sum(time_values)) * 100
        english_percent = (total_time_by_language['English'] / sum(time_values)) * 100
        
        wedges_time, texts_time, autotexts_time = plt.pie(time_values, 
                                                          labels=time_labels,
                                                          colors=time_colors,
                                                          autopct='%1.1f%%',
                                                          startangle=90,
                                                          explode=(0.05, 0.05),
                                                          shadow=True)
        
        # Улучшаем текст
        for autotext in autotexts_time:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(12)
        
        for text in texts_time:
            text.set_fontsize(12)
            text.set_fontweight('bold')
        
        plt.title('⏱️ Распределение времени просмотра по языкам', 
                 fontsize=16, fontweight='bold', pad=20)
        
        # Форматируем время в читаемый вид
        def format_time_display(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            if hours > 0:
                return f"{hours}ч {minutes}м"
            else:
                return f"{minutes}м"
        
        russian_time_str = format_time_display(total_time_by_language['Russian'])
        english_time_str = format_time_display(total_time_by_language['English'])
        total_time_str = format_time_display(sum(time_values))
        
        # Добавляем статистику времени
        time_stats_text = f"Общее время: {total_time_str}\n🇷🇺 Русский: {russian_time_str}\n🇺🇸 English: {english_time_str}"
        plt.text(1.3, 0.5, time_stats_text, fontsize=11, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('watch_time_by_language.png', dpi=300, bbox_inches='tight')
        print("✅ График 'watch_time_by_language.png' создан")
        plt.close()
        
        print(f"\n🎯 Все графики успешно созданы!")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        print("Убедитесь, что установлены pandas и matplotlib:")
        print("pip install pandas matplotlib")

if __name__ == "__main__":
    print("=== Создание графиков для анализа YouTube ===\n")
    create_youtube_graphs() 