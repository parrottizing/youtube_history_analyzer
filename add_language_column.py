import csv
import sys
import re

# Fix Unicode encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def detect_language(text):
    """
    Определяет язык текста на основе используемых символов.
    
    Args:
        text (str): Текст для анализа
        
    Returns:
        str: 'Russian' если найдены кириллические символы, иначе 'English'
    """
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
    
    Args:
        input_file (str): Имя входного CSV файла.
        output_file (str): Имя выходного CSV файла с добавленной колонкой языка.
    """
    print(f"Читаю данные из файла '{input_file}'...")
    
    try:
        updated_rows = []
        
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)  # Читаем заголовок
            
            # Добавляем новую колонку в заголовок
            new_header = header + ['Language']
            updated_rows.append(new_header)
            
            print(f"Исходные колонки: {header}")
            print(f"Новые колонки: {new_header}")
            
            # Обрабатываем каждую строку данных
            processed_count = 0
            russian_count = 0
            english_count = 0
            
            for row in reader:
                if len(row) >= 1:  # Убеждаемся, что есть название видео
                    video_title = row[0]  # Первая колонка - название видео
                    language = detect_language(video_title)
                    
                    # Добавляем язык к строке
                    new_row = row + [language]
                    updated_rows.append(new_row)
                    
                    # Ведем статистику
                    processed_count += 1
                    if language == 'Russian':
                        russian_count += 1
                    else:
                        english_count += 1
                    
                    # Показываем прогресс для первых нескольких записей
                    if processed_count <= 5:
                        print(f"  {processed_count}. '{video_title[:50]}...' -> {language}")
                
        print(f"\nОбработано {processed_count} записей:")
        print(f"  Русских видео: {russian_count}")
        print(f"  Английских видео: {english_count}")
        
        # Записываем обновленные данные в новый файл
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
        
        print(f"\nДанные с добавленной колонкой 'Language' сохранены в файле '{output_file}'")
        
        # Показываем примеры для проверки
        print(f"\nПримеры определения языка:")
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            print(f"Первые несколько записей:")
            for i, row in enumerate(reader):
                if i < 10 and len(row) >= 4:  # Показываем первые 10 записей
                    title = row[0][:40] + "..." if len(row[0]) > 40 else row[0]
                    channel = row[1]
                    language = row[3]  # Новая колонка Language
                    print(f"  {title} | {channel} | {language}")
                elif i >= 10:
                    break
                    
    except FileNotFoundError:
        print(f"\nОШИБКА: Файл '{input_file}' не найден.")
        print("Сначала запустите remove_duplicates.py для создания очищенного CSV файла.")
        return
        
    except Exception as e:
        print(f"\nОШИБКА при обработке файла: {e}")
        return

def test_language_detection():
    """
    Тестирует функцию определения языка на примерах.
    """
    print("=== Тестирование определения языка ===")
    
    test_cases = [
        "How AI Coding Agents Will Change Your Job",
        "Ян Зубков «ЧЕРНЫЙ СТЕНДАП»",
        "The Mental Health AI Chatbot Made for Real Life",
        "Главная Загадка Второй Мировой.",
        "I/O '25 in under 10 minutes",
        "Почему принимать витамины бесполезно и опасно?",
        "Franz Hermann is back (laughing)",
        "Имола 2025 Обзор гонки"
    ]
    
    for test_text in test_cases:
        language = detect_language(test_text)
        print(f"'{test_text}' -> {language}")
    
    print()

if __name__ == "__main__":
    print("=== Добавление колонки 'Language' в историю YouTube ===\n")
    
    # Сначала тестируем определение языка
    test_language_detection()
    
    # Затем обрабатываем файл
    add_language_column() 