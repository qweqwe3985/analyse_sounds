import os
import io

from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import librosa
import utils
import json
import csv

from yamnet import YamnetInstance


from bot import init_bot, trigger_broadcast
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Словарь категорий для фильтрации проверки
categories = {"Explosion", "Eruption", "Firecracker", "Crackle", "Shatter"}

# Путь для сохранения файлов и CSV
BASE_DIR = Path("audio_data")
CSV_FILE = BASE_DIR / "audio_metadata.csv"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: заменить бы потом на норм адреса из env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yamnet = YamnetInstance()

# Создаем CSV-файл с заголовками, если он не существует
if not CSV_FILE.exists():
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Coordinates", "Date", "Time", "Category"])


@app.get("/download/")
async def download_file(filename: str):
    file_path = f"files/{filename}"
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path, filename=filename, media_type="application/octet-stream"
        )
    return {"error": "File not found"}


@app.post("/upload-audio/")
async def upload_file(coordinates: str = Form(None), file: UploadFile = File(...)):

    response = {}
    file_content = await file.read()
    audio_buffer = io.BytesIO(file_content)
    # Декодируем JSON
    coords = json.loads(coordinates)
    lat, lon = coords

    try:
        y, sr, duration = utils.librosa_analyse(audio_buffer)
        response["librosa"] = {
            "filename": file.filename,
            "duration": duration,
            "sample_rate": sr,
        }
        print(response["librosa"])

        scores, class_names = yamnet.analyze_audio(y)
        response["best_scores"] = utils.analyse_best(class_names, scores)

        # Сохранение аудиофайла и запись в CSV
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        coords_dir = BASE_DIR / f"{lat}_{lon}" / date_str
        coords_dir.mkdir(parents=True, exist_ok=True)

        # Сохраняем аудиофайл
        audio_filename = coords_dir / f"{time_str}.wav"
        with open(audio_filename, "wb") as audio_file:
            audio_file.write(file_content)

        # Записываем информацию в CSV
        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [f"{lat},{lon}", date_str, time_str, response["best_scores"]]
            )

    except Exception as e:
        response = {"error": str(e)}

    print(response)
    if utils.check_categories(response["best_scores"], categories):
        try:
            message = f'Сообытие: {utils.check_categories(response["best_scores"], categories)} \n Координаты: {lat}, {lon} \n <a href="https://yandex.ru/maps/?ll={lon},{lat}&z=12&l=map">Карта</a>'
            print("creating application")
            application = (
                ApplicationBuilder()
                .token("7545487742:AAHK31bh5-4YddWAiUJKXBjJVKMQ0bF8beE")
                .build()
            )
            print("sending broadcast")
            await trigger_broadcast(application, message)
            print("broadcast sended")
        except Exception as e:
            print(e)

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
    yamnet_model = hub.load("https://tfhub.dev/google/yamnet/1")
