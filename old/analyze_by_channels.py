import csv
import sys
from collections import defaultdict
import re

# Fix Unicode encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def parse_duration(duration_str):
    """
    Парсит строку длительности видео и возвращает общее количество секунд.
    
    Args:
        duration_str (str): Строка формата "12:34" или "1:23:45"
        
    Returns:
        int: Общее количество секунд
    """
    try:
        parts = duration_str.strip().split(':')
        if len(parts) == 2:  # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 0
    except:
        return 0

def format_duration(total_seconds):
    """
    Форматирует количество секунд в читаемый формат.
    
    Args:
        total_seconds (int): Общее количество секунд
        
    Returns:
        str: Форматированная строка времени
    """
    if total_seconds == 0:
        return "0:00"
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def analyze_channels(input_file='youtube_history_with_language.csv'):
    """
    Анализирует историю YouTube по каналам.
    
    Args:
        input_file (str): Имя входного CSV файла с данными о видео.
    """
    print(f"Читаю данные из файла '{input_file}'...")
    
    try:
        # Структура для хранения данных по каналам
        channels_data = defaultdict(lambda: {
            'videos': [],
            'total_duration': 0,
            'languages': set(),
            'video_count': 0
        })
        
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                channel = row['Название канала'].strip()
                video_title = row['Название видео'].strip()
                duration_str = row['Длительность видео'].strip()
                language = row['Language'].strip()
                
                # Парсим длительность
                duration_seconds = parse_duration(duration_str)
                
                # Добавляем данные к каналу
                channels_data[channel]['videos'].append({
                    'title': video_title,
                    'duration': duration_str,
                    'duration_seconds': duration_seconds,
                    'language': language
                })
                channels_data[channel]['total_duration'] += duration_seconds
                channels_data[channel]['languages'].add(language)
                channels_data[channel]['video_count'] += 1
        
        # Сортируем каналы по количеству видео (убывание)
        sorted_channels = sorted(channels_data.items(), 
                               key=lambda x: x[1]['video_count'], 
                               reverse=True)
        
        print(f"\nНайдено {len(sorted_channels)} уникальных каналов")
        print("=" * 80)
        
        # Выводим топ каналов
        print("\nТОП КАНАЛОВ ПО КОЛИЧЕСТВУ ПРОСМОТРЕННЫХ ВИДЕО:")
        print("-" * 80)
        
        total_videos = sum(data['video_count'] for _, data in sorted_channels)
        total_watch_time = sum(data['total_duration'] for _, data in sorted_channels)
        
        for i, (channel, data) in enumerate(sorted_channels[:10], 1):
            percentage = (data['video_count'] / total_videos) * 100
            languages_str = ', '.join(sorted(data['languages']))
            
            print(f"{i:2d}. {channel}")
            print(f"    Видео: {data['video_count']} ({percentage:.1f}%)")
            print(f"    Время: {format_duration(data['total_duration'])}")
            print(f"    Языки: {languages_str}")
            print()
        
        # Сохраняем детальный отчет в CSV
        output_file = 'channel_analysis.csv'
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Канал', 
                'Количество видео', 
                'Общее время просмотра', 
                'Общее время (секунды)',
                'Языки',
                'Процент от общего количества видео'
            ])
            
            for channel, data in sorted_channels:
                percentage = (data['video_count'] / total_videos) * 100
                languages_str = ', '.join(sorted(data['languages']))
                
                writer.writerow([
                    channel,
                    data['video_count'],
                    format_duration(data['total_duration']),
                    data['total_duration'],
                    languages_str,
                    f"{percentage:.1f}%"
                ])
        
        print(f"Детальный отчет сохранен в файле '{output_file}'")
        
        # Сохраняем подробный список видео по каналам
        detailed_file = 'videos_by_channel.csv'
        with open(detailed_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Канал', 
                'Название видео', 
                'Длительность', 
                'Язык'
            ])
            
            for channel, data in sorted_channels:
                for video in data['videos']:
                    writer.writerow([
                        channel,
                        video['title'],
                        video['duration'],
                        video['language']
                    ])
        
        print(f"Подробный список видео сохранен в файле '{detailed_file}'")
        
        # Статистика по языкам
        print(f"\nОБЩАЯ СТАТИСТИКА:")
        print("-" * 40)
        print(f"Всего каналов: {len(sorted_channels)}")
        print(f"Всего видео: {total_videos}")
        print(f"Общее время просмотра: {format_duration(total_watch_time)}")
        
        # Анализ по языкам
        language_stats = defaultdict(lambda: {'channels': set(), 'videos': 0, 'time': 0})
        for channel, data in sorted_channels:
            for video in data['videos']:
                lang = video['language']
                language_stats[lang]['channels'].add(channel)
                language_stats[lang]['videos'] += 1
                language_stats[lang]['time'] += video['duration_seconds']
        
        print(f"\nСТАТИСТИКА ПО ЯЗЫКАМ:")
        print("-" * 40)
        for lang, stats in language_stats.items():
            print(f"{lang}:")
            print(f"  Видео: {stats['videos']}")
            print(f"  Каналы: {len(stats['channels'])}")
            print(f"  Время: {format_duration(stats['time'])}")
            print()
        
        # Показываем каналы с наибольшим временем просмотра
        print(f"\nТОП КАНАЛОВ ПО ВРЕМЕНИ ПРОСМОТРА:")
        print("-" * 50)
        sorted_by_time = sorted(channels_data.items(), 
                              key=lambda x: x[1]['total_duration'], 
                              reverse=True)
        
        for i, (channel, data) in enumerate(sorted_by_time[:5], 1):
            time_percentage = (data['total_duration'] / total_watch_time) * 100
            print(f"{i}. {channel}")
            print(f"   {format_duration(data['total_duration'])} ({time_percentage:.1f}%)")
            print(f"   {data['video_count']} видео")
            print()
            
    except FileNotFoundError:
        print(f"\nОШИБКА: Файл '{input_file}' не найден.")
        print("Сначала запустите add_language_column.py для создания файла с языками.")
        return
        
    except Exception as e:
        print(f"\nОШИБКА при обработке файла: {e}")
        return

if __name__ == "__main__":
    print("=== Анализ YouTube истории по каналам ===\n")
    analyze_channels() 