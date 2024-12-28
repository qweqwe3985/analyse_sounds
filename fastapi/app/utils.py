import librosa
import io
import numpy as np


def analyse_best(class_names, scores):
    # Определяем топ-5 распознанных звуков
    mean_scores = scores.mean(axis=0)
    top_indices = np.argsort(mean_scores)[-5:][::-1]

    return [f"{class_names[i]}: {mean_scores[i]:.2f}" for i in top_indices]


def librosa_analyse(audio, sr=16000):
    waveform = sample_rate = duration = None
    try:
        if isinstance(audio, str):
            waveform, sample_rate = librosa.load(audio, sr=sr)
        elif isinstance(audio, io.BytesIO):
            waveform, sample_rate = librosa.load(audio, sr=sr)
        else:
            raise TypeError("Argument must be str or io.BytesIO")

        duration = (librosa.get_duration(y=waveform),)
        return (waveform, sample_rate, duration)

    except Exception as e:
        print(e)
        return None


# Функция для проверки наличия категорий
def check_categories(response_list, categories):
    found_categories = set()  # Множество для найденных категорий
    for item in response_list:
        for category in categories:
            if category.lower() in item.lower():  # Поиск без учета регистра
                found_categories.add(category)
    return found_categories if found_categories else False