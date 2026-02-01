import csv
import sys
import pandas as pd

# Fix Unicode encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def remove_duplicates(input_file='youtube_history.csv', output_file='youtube_history_clean.csv'):
    """
    Удаляет дубликаты видео из CSV файла.
    Дубликатами считаются записи с одинаковым названием видео и названием канала.
    
    Args:
        input_file (str): Имя входного CSV файла.
        output_file (str): Имя выходного CSV файла для сохранения очищенных данных.
    """
    print(f"Читаю данные из файла '{input_file}'...")
    
    try:
        # Читаем CSV файл
        df = pd.read_csv(input_file, encoding='utf-8-sig')
        
        print(f"Загружено {len(df)} записей")
        
        # Показываем структуру данных
        print(f"Колонки: {list(df.columns)}")
        
        # Удаляем дубликаты на основе названия видео и канала
        # keep='first' означает, что сохраняем первое вхождение
        df_clean = df.drop_duplicates(subset=['Название видео', 'Название канала'], keep='first')
        
        duplicates_removed = len(df) - len(df_clean)
        
        print(f"\nОбнаружено и удалено {duplicates_removed} дубликатов")
        print(f"Осталось {len(df_clean)} уникальных записей")
        
        # Если дубликатов не было, сообщаем об этом
        if duplicates_removed == 0:
            print("Дубликаты не найдены. Файл уже содержит только уникальные записи.")
            return
        
        # Сохраняем очищенные данные
        df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\nОчищенные данные сохранены в файле '{output_file}'")
        
        # Показываем примеры удаленных дубликатов
        if duplicates_removed > 0:
            print(f"\nПримеры удаленных дубликатов:")
            # Находим дубликаты для демонстрации
            duplicated_mask = df.duplicated(subset=['Название видео', 'Название канала'], keep=False)
            duplicates_df = df[duplicated_mask].sort_values(['Название видео', 'Название канала'])
            
            # Показываем первые несколько дубликатов
            if len(duplicates_df) > 0:
                print(duplicates_df[['Название видео', 'Название канала']].head(10).to_string(index=False))
            
    except FileNotFoundError:
        print(f"\nОШИБКА: Файл '{input_file}' не найден.")
        print("Сначала запустите parser.py для создания CSV файла.")
        return
        
    except Exception as e:
        print(f"\nОШИБКА при обработке файла: {e}")
        return

def remove_duplicates_manual(input_file='youtube_history.csv', output_file='youtube_history_clean.csv'):
    """
    Альтернативная функция для удаления дубликатов без использования pandas.
    Использует только стандартные библиотеки Python.
    """
    print(f"Читаю данные из файла '{input_file}' (ручной метод)...")
    
    try:
        seen_videos = set()  # Множество для отслеживания уже виденных видео
        unique_rows = []
        duplicates_count = 0
        
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)  # Читаем заголовок
            unique_rows.append(header)
            
            for row in reader:
                if len(row) >= 2:  # Убеждаемся, что в строке достаточно колонок
                    video_title = row[0].strip()
                    channel_name = row[1].strip()
                    
                    # Создаем уникальный ключ из названия видео и канала
                    video_key = (video_title, channel_name)
                    
                    if video_key not in seen_videos:
                        seen_videos.add(video_key)
                        unique_rows.append(row)
                    else:
                        duplicates_count += 1
        
        print(f"Загружено {len(unique_rows) - 1 + duplicates_count} записей")
        print(f"Обнаружено и удалено {duplicates_count} дубликатов")
        print(f"Осталось {len(unique_rows) - 1} уникальных записей")
        
        # Записываем очищенные данные
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(unique_rows)
        
        print(f"\nОчищенные данные сохранены в файле '{output_file}'")
        
    except FileNotFoundError:
        print(f"\nОШИБКА: Файл '{input_file}' не найден.")
        print("Сначала запустите parser.py для создания CSV файла.")
        return
        
    except Exception as e:
        print(f"\nОШИБКА при обработке файла: {e}")
        return

if __name__ == "__main__":
    print("=== Удаление дубликатов из истории YouTube ===\n")
    
    try:
        # Пытаемся использовать pandas для более эффективной работы
        import pandas as pd
        remove_duplicates()
    except ImportError:
        # Если pandas не установлен, используем ручной метод
        print("Pandas не установлен. Используем альтернативный метод...\n")
        remove_duplicates_manual() 