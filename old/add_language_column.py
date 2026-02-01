import csv
import sys
import re

# Fix Unicode encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def has_meaningful_words(text):
    """
    Проверяет, содержит ли текст значимые слова (буквы).
    
    Args:
        text (str): Текст для анализа
        
    Returns:
        bool: True если найдены буквы, False если только числа/символы
    """
    # Ищем любые буквы (латинские или кириллические)
    letter_pattern = re.compile(r'[a-zA-Zа-яёА-ЯЁ]')
    return bool(letter_pattern.search(text))

def detect_language(text):
    """
    Определяет язык текста на основе используемых символов.
    
    Args:
        text (str): Текст для анализа
        
    Returns:
        str|None: 'Russian' если найдены кириллические символы, 
                  'English' если найдены латинские буквы,
                  None если нет значимых слов (только цифры/символы)
    """
    # Проверяем, есть ли в тексте значимые слова
    if not has_meaningful_words(text):
        return None  # Нельзя определить язык - нет букв
    
    # Убираем пробелы, знаки препинания и цифры для анализа только букв
    cleaned_text = re.sub(r'[^\w]', '', text)
    
    # Проверяем наличие кириллических символов
    cyrillic_pattern = re.compile(r'[а-яё]', re.IGNORECASE)
    
    if cyrillic_pattern.search(cleaned_text):
        return 'Russian'
    else:
        return 'English'

def add_language_column(input_file='youtube_history_clean.csv', output_file='youtube_history_with_language.csv'):
    """
    Добавляет колонку 'Language' в CSV файл с историей YouTube.
    Использует канальную стратегию для видео без определимого языка в названии.
    
    Args:
        input_file (str): Имя входного CSV файла.
        output_file (str): Имя выходного CSV файла с добавленной колонкой языка.
    """
    print(f"📖 Читаю данные из файла '{input_file}'...")
    
    try:
        all_rows = []
        channel_languages = {}  # Словарь для отслеживания языков по каналам
        
        # Первый проход: читаем все данные и определяем язык где возможно
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)  # Читаем заголовок
            
            print(f"Исходные колонки: {header}")
            print(f"Новые колонки: {header + ['Language']}")
            
            for row in reader:
                if len(row) >= 2:  # Убеждаемся, что есть название видео и канал
                    video_title = row[0]  # Первая колонка - название видео
                    channel_name = row[1]  # Вторая колонка - название канала
                    
                    # Пытаемся определить язык
                    detected_language = detect_language(video_title)
                    
                    # Сохраняем данные для второго прохода
                    all_rows.append({
                        'row': row,
                        'title': video_title,
                        'channel': channel_name,
                        'detected_language': detected_language
                    })
                    
                    # Если язык определен, добавляем к профилю канала
                    if detected_language:
                        if channel_name not in channel_languages:
                            channel_languages[channel_name] = {'Russian': 0, 'English': 0}
                        channel_languages[channel_name][detected_language] += 1

        # Определяем доминирующий язык для каждого канала
        channel_primary_language = {}
        for channel, lang_counts in channel_languages.items():
            if lang_counts['Russian'] > lang_counts['English']:
                channel_primary_language[channel] = 'Russian'
            elif lang_counts['English'] > lang_counts['Russian']:
                channel_primary_language[channel] = 'English'
            else:
                # При равенстве оставляем Russian как дефолт для каналов с кириллицей в названии
                if has_meaningful_words(channel) and detect_language(channel) == 'Russian':
                    channel_primary_language[channel] = 'Russian'
                else:
                    channel_primary_language[channel] = 'English'

        print(f"🔍 Анализ каналов завершен. Найдено {len(channel_primary_language)} каналов с определенным языком.")
        
        # Второй проход: назначаем язык всем видео
        updated_rows = [header + ['Language']]  # Заголовок
        processed_count = 0
        russian_count = 0
        english_count = 0
        fallback_count = 0
        
        for row_data in all_rows:
            detected_language = row_data['detected_language']
            channel_name = row_data['channel']
            video_title = row_data['title']
            
            # Если язык не определен по названию видео, используем канальную стратегию
            if detected_language is None:
                if channel_name in channel_primary_language:
                    final_language = channel_primary_language[channel_name]
                    fallback_count += 1
                else:
                    # Если даже для канала нет данных, пытаемся определить по названию канала
                    channel_detected = detect_language(channel_name)
                    final_language = channel_detected if channel_detected else 'English'
                    fallback_count += 1
            else:
                final_language = detected_language
            
            # Добавляем язык к строке
            new_row = row_data['row'] + [final_language]
            updated_rows.append(new_row)
            
            # Ведем статистику
            processed_count += 1
            if final_language == 'Russian':
                russian_count += 1
            else:
                english_count += 1
            
            # Показываем прогресс для проблемных случаев
            if detected_language is None and processed_count <= 10:
                print(f"  🔄 '{video_title[:30]}...' (канал: {channel_name}) -> {final_language} (по каналу)")
                
        print(f"\n📊 Статистика обработки:")
        print(f"  • Всего видео: {processed_count}")
        print(f"  • Русских видео: {russian_count}")
        print(f"  • Английских видео: {english_count}")
        print(f"  • Определено по каналу: {fallback_count}")
        
        # Записываем обновленные данные в новый файл
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
        
        print(f"\n✅ Данные с добавленной колонкой 'Language' сохранены в файле '{output_file}'")
        
        # Показываем примеры для проверки
        print(f"\n🔍 Примеры определения языка:")
        print(f"Первые несколько записей:")
        for i, row in enumerate(updated_rows[1:11]):  # Пропускаем заголовок, показываем первые 10
            if len(row) >= 4:
                title = row[0][:30] + "..." if len(row[0]) > 30 else row[0]
                channel = row[1][:15] + "..." if len(row[1]) > 15 else row[1]
                language = row[3]  # Новая колонка Language
                print(f"  {title:35} | {channel:18} | {language}")
                
    except FileNotFoundError:
        print(f"\n❌ ОШИБКА: Файл '{input_file}' не найден.")
        print("Сначала запустите remove_duplicates.py для создания очищенного CSV файла.")
        return
        
    except Exception as e:
        print(f"\n❌ ОШИБКА при обработке файла: {e}")
        return

def test_language_detection():
    """
    Тестирует функцию определения языка на примерах.
    """
    print("=== Тестирование определения языка ===")
    
    test_cases = [
        ("How AI Coding Agents Will Change Your Job", "Обычный английский текст"),
        ("Ян Зубков «ЧЕРНЫЙ СТЕНДАП»", "Обычный русский текст"),
        ("The Mental Health AI Chatbot Made for Real Life", "Английский с цифрами"),
        ("Главная Загадка Второй Мировой.", "Русский с знаками препинания"),
        ("I/O '25 in under 10 minutes", "Английский с символами"),
        ("Почему принимать витамины бесполезно и опасно?", "Русский с вопросом"),
        ("97%", "Проблемный случай - только цифры и символы"),
        ("123", "Только цифры"),
        ("!@#$%", "Только символы"),
        ("2025", "Год"),
        ("Franz Hermann is back (laughing)", "Английский в скобках"),
        ("Имола 2025 Обзор гонки", "Русский с цифрами"),
        ("100K Subscribers!", "Английский с символами"),
        ("🎉🎊🎈", "Только эмодзи"),
        ("", "Пустая строка")
    ]
    
    print("Результаты тестирования:")
    print("=" * 80)
    
    for test_text, description in test_cases:
        language = detect_language(test_text)
        has_words = has_meaningful_words(test_text)
        
        status = "✅" if language else "❌"
        result = language if language else "None (нет значимых слов)"
        
        print(f"{status} '{test_text:35}' -> {result:10} | {description}")
    
    print("=" * 80)
    print("Примечание: 'None' означает, что нужно использовать канальную стратегию")
    print()

if __name__ == "__main__":
    print("=== Добавление колонки 'Language' в историю YouTube ===\n")
    
    # Сначала тестируем определение языка
    test_language_detection()
    
    # Затем обрабатываем файл
    add_language_column() 