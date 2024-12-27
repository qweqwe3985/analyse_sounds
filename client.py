import pyaudio
import numpy as np
import requests
import wave
import threading
import queue
import logging
from io import BytesIO
import keyboard

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Конфигурация
CHUNK = 1024  # Количество фреймов в одном блоке
FORMAT = pyaudio.paInt16  # Формат аудио данных
CHANNELS = 1  # Количество каналов (моно)
RATE = 16000  # Частота дискретизации
THRESHOLD = 100  # Порог громкости для срабатывания
PRE_BUFFER_SECONDS = 10  # Количество секунд до события
POST_BUFFER_SECONDS = 5  # Количество секунд после события
SERVER_URL = "http://127.0.0.1:8000/upload-audio/"  # URL сервера для загрузки аудио

# Координаты (широта, долгота)
COORDINATES = (55.7558, 37.6173)  # Пример: Москва

# Очередь для хранения аудио данных
audio_queue = queue.Queue()

# Флаг для управления выполнением скрипта
running = True

def save_audio_to_wav(audio_data, filename):
    """Сохраняет аудио данные в WAV файл."""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 2 байта для формата paInt16
        wf.setframerate(RATE)
        wf.writeframes(audio_data.tobytes())
    logging.info(f"Аудио сохранено в файл: {filename}")

def send_audio_data(audio_data, coordinates):
    """Отправляет аудио данные и координаты на сервер."""
    # Сохраняем аудио в WAV файл в памяти
    audio_buffer = BytesIO()
    with wave.open(audio_buffer, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 2 байта для формата paInt16
        wf.setframerate(RATE)
        wf.writeframes(audio_data.tobytes())
    audio_buffer.seek(0)

    # Подготавливаем данные для отправки
    files = {'file': ('audio.wav', audio_buffer, 'audio/wav')}
    data = {'coordinates': f"{coordinates[0]},{coordinates[1]}"}

    try:
        response = requests.post(SERVER_URL, files=files, data=data)
        logging.info(f"Данные отправлены на сервер. Ответ: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error(f"Ошибка при отправке данных: {e}")
    finally:
        audio_buffer.close()

def audio_callback(in_data, frame_count, time_info, status):
    """Callback функция для обработки аудио данных."""
    audio_data = np.frombuffer(in_data, dtype=np.int16)
    audio_queue.put(audio_data)
    return (in_data, pyaudio.paContinue)

def monitor_audio():
    """Мониторинг аудио потока на резкие повышения громкости."""
    global running

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=audio_callback)

    buffer = []
    logging.info("Начало мониторинга аудио...")
    while running:
        audio_data = audio_queue.get()
        buffer.append(audio_data)
        if len(buffer) > (RATE // CHUNK) * (PRE_BUFFER_SECONDS + POST_BUFFER_SECONDS):
            buffer.pop(0)

        # Проверка на резкое повышение громкости
        if np.max(audio_data) > THRESHOLD:
            logging.info("Обнаружено резкое повышение громкости!")
            # Записываем ещё 10 секунд после срабатывания
            for _ in range((RATE // CHUNK) * POST_BUFFER_SECONDS):
                if not running:
                    break
                audio_data = audio_queue.get()
                buffer.append(audio_data)

            # Вырезаем предыдущие 5 секунд и следующие 10 секунд
            start_index = max(0, len(buffer) - (RATE // CHUNK) * (PRE_BUFFER_SECONDS + POST_BUFFER_SECONDS))
            selected_data = np.concatenate(buffer[start_index:])
            # Отправляем данные на сервер
            send_audio_data(selected_data, COORDINATES)
            # Очищаем буфер после отправки
            buffer.clear()

    stream.stop_stream()
    stream.close()
    p.terminate()
    logging.info("Мониторинг аудио завершён.")

def exit_handler():
    """Обработчик для завершения скрипта по Ctrl + D."""
    global running
    logging.info("Обнаружено нажатие Ctrl + D. Завершение работы...")
    running = False

if __name__ == "__main__":
    # Регистрируем обработчик для Ctrl + D
    keyboard.add_hotkey('ctrl+d', exit_handler)

    # Запуск мониторинга аудио в отдельном потоке
    audio_thread = threading.Thread(target=monitor_audio)
    audio_thread.start()
    audio_thread.join()