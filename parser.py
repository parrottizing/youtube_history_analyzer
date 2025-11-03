import csv
import sys
import re

# Fix Unicode encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

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
    stripped_lines = [line.strip() for line in lines]
    day_markers = {
        "Today",
        "Yesterday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
        "Сегодня",
        "Вчера",
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    }
    skip_markers = {"•", "Mark as watched"}

    def next_non_empty_index(start, extra_skip=None):
        skip_values = day_markers | skip_markers
        if extra_skip:
            skip_values |= extra_skip
        for idx in range(start, len(stripped_lines)):
            value = stripped_lines[idx]
            if not value:
                continue
            if value in skip_values:
                continue
            return idx
        return None

    # Проходим по всем строкам и ищем длительности как маркеры начала записи
    for i, value in enumerate(stripped_lines):
        if not is_timestamp(value):
            continue

        duration = value

        title_idx = next_non_empty_index(i + 1)
        if title_idx is None:
            continue
        title = stripped_lines[title_idx]

        channel_idx = next_non_empty_index(
            title_idx + 1, extra_skip={"Mark as watched"}
        )
        if channel_idx is None:
            continue
        channel_line = stripped_lines[channel_idx]
        # Канал иногда указывается вместе с символом •, поэтому обрезаем его
        channel = channel_line.split("•")[0].strip()

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
