import csv
import re

def is_timestamp(text):
    """
    Проверяет, является ли строка временной меткой (например, "7:20" или "1:34:37").
    Это помогает отфильтровать SHORTS, у которых вместо времени написано "SHORTS".
    """
    # Паттерн: одна или больше цифр, двоеточие, две цифры.
    # И опционально еще одно двоеточие и две цифры для часов.
    return re.match(r'^\d+:\d{2}(:\d{2})?$', text.strip()) is not None

def parse_youtube_history(input_file='history.txt', output_file='youtube_history.csv'):
    """
    Основная функция для парсинга истории просмотров YouTube.
    
    Args:
        input_file (str): Имя входного файла с историей.
        output_file (str): Имя выходного CSV-файла для сохранения результатов.
    """
    print(f"Читаю данные из файла '{input_file}'...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"\nОШИБКА: Файл '{input_file}' не найден.")
        print("Пожалуйста, убедитесь, что вы создали этот файл и поместили его в ту же папку, что и скрипт.")
        # Создаем файл-инструкцию для пользователя
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write("Сюда вставьте вашу историю просмотров из YouTube и запустите скрипт снова.")
        print(f"Я создал для вас файл '{input_file}'. Вставьте в него текст и попробуйте еще раз.")
        return

    extracted_data = []
    
    # Проходим по всем строкам, используя индекс, чтобы смотреть на соседние строки
    for i, line in enumerate(lines):
        if "Now playing" in line:
            # Убедимся, что мы не выходим за пределы списка
            if i == 0:
                continue

            # Строка выше - потенциальная длительность
            potential_duration = lines[i-1].strip()

            # Проверяем, является ли строка выше временной меткой. Если нет - это SHORTS, пропускаем.
            if not is_timestamp(potential_duration):
                continue

            # Если проверка пройдена, извлекаем данные
            duration = potential_duration
            
            # Строка ниже - название видео (но сначала проверим на "Mark as watched")
            title_line_index = i + 1
            
            # Проверяем, есть ли "Mark as watched" в следующей строке
            if title_line_index < len(lines) and "Mark as watched" in lines[title_line_index]:
                # Пропускаем "Mark as watched" и ищем следующую непустую строку с названием
                title_line_index += 1
                # Ищем первую непустую строку после "Mark as watched"
                while title_line_index < len(lines) and not lines[title_line_index].strip():
                    title_line_index += 1
            
            # Получаем название видео
            if title_line_index < len(lines):
                title = lines[title_line_index].strip()
            else:
                continue  # Если не нашли название, пропускаем эту запись
            
            # Ищем название канала в следующих строках
            channel = ""
            # Начинаем поиск со строки после названия видео
            for j in range(title_line_index + 1, len(lines)):
                channel_line = lines[j].strip()
                # Первая же непустая строка - это то, что нам нужно
                if channel_line:
                    # Название канала - это все до символа '•'
                    channel = channel_line.split('•')[0].strip()
                    break # Нашли канал, выходим из внутреннего цикла
            
            # Добавляем найденные данные в наш список
            if title and channel and duration:
                extracted_data.append([title, channel, duration])

    if not extracted_data:
        print("Не найдено ни одной записи о видео. Проверьте формат данных в файле 'history.txt'.")
        return

    # Записываем все найденные данные в CSV-файл
    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            # Записываем заголовок таблицы
            writer.writerow(['Название видео', 'Название канала', 'Длительность видео'])
            # Записываем все строки с данными
            writer.writerows(extracted_data)
        
        print(f"\nГотово! Извлечено {len(extracted_data)} записей.")
        print(f"Результат сохранен в файле '{output_file}'")

    except PermissionError:
        print(f"\nОШИБКА: Не удалось записать файл '{output_file}'.")
        print("Возможно, он открыт в другой программе (например, в Excel). Закройте его и попробуйте снова.")


# Эта строка запускает нашу основную функцию при запуске скрипта
if __name__ == "__main__":
    parse_youtube_history()