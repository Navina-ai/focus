import wave
import os
import io
import numpy as np
import av

def save_audio_to_file(audio_data, file_name, audio_dir="audio_files", audio_format="wav"):
    """
    Saves the audio data to a file.

    :param client_id: Unique identifier for the client.
    :param audio_data: The audio data to save.
    :param file_counters: Dictionary to keep track of file counts for each client.
    :param audio_dir: Directory where audio files will be saved.
    :param audio_format: Format of the audio file.
    :return: Path to the saved audio file.
    """

    os.makedirs(audio_dir, exist_ok=True)
    
    file_path = os.path.join(audio_dir, file_name)

    with wave.open(file_path, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Assuming mono audio
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(audio_data)

    return file_path


def bytearray_audio_to_nparray(audio_data, target_sample_rate, original_sample_rate=16000, split_stereo=False):
    """
    Converts a bytearray of audio data into a numpy array with resampling.

    Args:
        audio_data (bytearray): The raw audio data.
        target_sample_rate (int): The desired sample rate for the output audio.
        original_sample_rate (int): The original sample rate of the input audio.
        split_stereo (bool): If true, returns separate left and right channels.

    Returns:
        np.ndarray: A numpy array containing the resampled audio. If split_stereo is true,
                    returns a tuple with left and right channels.
    """
    # Create an audio frame directly
    frame = av.AudioFrame(format='s16', layout='mono', samples=len(audio_data) // 2)
    frame.planes[0].update(audio_data)
    frame.sample_rate = original_sample_rate

    # Resample if needed
    if original_sample_rate != target_sample_rate or split_stereo:
        resampler = av.AudioResampler(
            format='s16',
            layout='stereo' if split_stereo else 'mono',
            rate=target_sample_rate
        )
        frame = resampler.resample(frame)

    # Convert the audio frame to a numpy array
    array = frame.to_ndarray()
    audio = array.astype(np.float32) / 32768.0  # Normalize to [-1, 1]

    if split_stereo:
        left_channel = audio[0::2]
        right_channel = audio[1::2]
        return (left_channel, right_channel)

    return audio[0]