import os
import io

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import librosa
from yamnet import YamnetInstance
import utils

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: заменить бы потом на норм адреса из env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yamnet = YamnetInstance()


@app.get("/download/")
async def download_file(filename: str):
    file_path = f"files/{filename}"
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path, filename=filename, media_type="application/octet-stream"
        )
    return {"error": "File not found"}


@app.post("/upload-audio/")
async def upload_file(file: UploadFile = File(...)):

    if file.content_type not in ["audio/wav", "audio/mp3", "audio/flac"]:
        return {
            "error": "Unsupported file format. Please upload a .wav, .mp3, or .flac file."
        }

    response = {}
    file_content = await file.read()
    audio_buffer = io.BytesIO(file_content)

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

    except Exception as e:
        response = {"error": str(e)}

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
    yamnet_model = hub.load("https://tfhub.dev/google/yamnet/1")
