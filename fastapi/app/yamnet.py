import numpy as np
import tensorflow as tf
import tensorflow_hub as hub


class YamnetInstance:
    def analyze_audio(self, waveform):
        scores, embeddings, spectrogram = self.yamnet_model(waveform)
        scores = np.array(scores)

        class_map_path = self.yamnet_model.class_map_path().numpy().decode("utf-8")
        class_names = [line.strip() for line in open(class_map_path)]

        return scores, class_names

    def __init__(self):
        self.yamnet_model = hub.load("https://tfhub.dev/google/yamnet/1")
