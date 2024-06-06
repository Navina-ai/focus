import os
from collections import defaultdict

import torch
import numpy as np
from pyannote.audio import Model, Inference
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from .spr_interface import SPRInterface


class PyannoteEmbeddingSPR(SPRInterface):
    """
    Pyannote-based implementation of the VADInterface.
    """

    def __init__(self, **kwargs):
        """
        Initializes Pyannote's VAD pipeline.

        Args:
            model_name (str): The model name for Pyannote.
            auth_token (str, optional): Authentication token for Hugging Face.
        """
        
        model_name = kwargs.get('model_name', "pyannote/embedding")
        self.max_speakers = kwargs.get('num_speakers', 2)
        self.threshold = kwargs.get('cosine_similarity_threshold', 0.3)
        auth_token = os.environ.get('PYANNOTE_AUTH_TOKEN')
        print("auth_token", auth_token)
        if not auth_token:
            auth_token = kwargs.get('auth_token')
        
        if auth_token is None:
            raise ValueError("Missing required env var in PYANNOTE_AUTH_TOKEN or argument in --vad-args: 'auth_token'")
        
        self._model = Model.from_pretrained(model_name, use_auth_token=auth_token)
        self.embedder = Inference(self.model.to(torch.device("cuda")), window="whole")
        self.client_embeddings = defaultdict(dict)
        self.client_num_speakers = defaultdict(lambda: 0)
        self.min_duration_frames_for_pred = kwargs.get('min_duration_spr_pred_sec', 0.2) * kwargs.get('sample_width', 2) * kwargs.get('sample_rate', 16000)
        self.min_duration_frames_for_save = kwargs.get('min_duration_spr_save__sec', 0.5) * kwargs.get('sample_width', 2) * kwargs.get('sample_rate', 16000)

    async def classify_speaker(self, client_id, audio_data):
        chosen_speaker = -1
        if len(audio_data) < self.min_duration_frames_for_pred:
            return chosen_speaker
        embedding = self.embedder.infer(torch.from_numpy(audio_data.reshape(1, -1)))

        new_embedding = normalize(embedding.reshape(1, -1))[0]
        embeddings = self.client_embeddings[client_id]
        # If no person has been initialized yet, initialize the first person
        if len(embeddings) == 0:
            embeddings[0] = {'sum': new_embedding, 'count': 1}
            self.client_num_speakers[client_id] = 1
            chosen_speaker = 0
        else:
            # Calculate current averages and normalize them
            current_averages = [embeddings[person_id]['sum'] / embeddings[person_id]['count']
                                for person_id in embeddings]
            current_averages = normalize(current_averages)

            # Calculate cosine similarities
            similarities = cosine_similarity([new_embedding], current_averages)[0]
            max_similarity = np.max(similarities)
            best_match = np.argmax(similarities)
            print(max_similarity)
            # If the best match similarity is above the threshold, update that person's data
            if max_similarity > self.threshold and embeddings[best_match]['count'] > self.min_duration_frames_for_save:
                embeddings[best_match]['sum'] += new_embedding
                embeddings[best_match]['count'] += 1
                chosen_speaker = int(best_match)
            else:
                # If there is only one person and the similarity is below the threshold, initialize the second person
                num_speakers = self.client_num_speakers[client_id]
                if num_speakers < self.max_speakers:
                    embeddings[num_speakers] = {'sum': new_embedding, 'count': 1}
                    self.client_num_speakers[client_id] += 1
                    chosen_speaker = num_speakers
                # If both persons are initialized, assign to the person with the highest similarity regardless of threshold
                else:
                    embeddings[best_match]['sum'] += new_embedding
                    embeddings[best_match]['count'] += 1
                    chosen_speaker = int(best_match)

        self.client_embeddings[client_id] = embeddings
        return chosen_speaker

    @property
    def model(self) -> Model:
        return self._model
