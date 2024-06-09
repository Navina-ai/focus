import os
import json
import time

import eventlet
from .buffering_strategy_interface import BufferingStrategyInterface

class SilenceAtEndOfChunk(BufferingStrategyInterface):
    """
    A buffering strategy that processes audio at the end of each chunk with silence detection.

    This class is responsible for handling audio chunks, detecting silence at the end of each chunk,
    and initiating the transcription process for the chunk.

    Attributes:
        client (Client): The client instance associated with this buffering strategy.
        chunk_length_seconds (float): Length of each audio chunk in seconds.
        chunk_offset_seconds (float): Offset time in seconds to be considered for processing audio chunks.
    """

    def __init__(self, client, transcription_callback=None, **kwargs):
        """
        Initialize the SilenceAtEndOfChunk buffering strategy.

        Args:
            client (Client): The client instance associated with this buffering strategy.
            **kwargs: Additional keyword arguments, including 'chunk_length_seconds' and 'chunk_offset_seconds'.
        """
        self.client = client

        self.chunk_length_seconds = os.environ.get('BUFFERING_CHUNK_LENGTH_SECONDS')
        if not self.chunk_length_seconds:
            self.chunk_length_seconds = kwargs.get('chunk_length_seconds')
        self.chunk_length_seconds = float(self.chunk_length_seconds)

        self.chunk_offset_seconds = os.environ.get('BUFFERING_CHUNK_OFFSET_SECONDS')
        if not self.chunk_offset_seconds:
            self.chunk_offset_seconds = kwargs.get('chunk_offset_seconds')
        self.chunk_offset_seconds = float(self.chunk_offset_seconds)

        self.error_if_not_realtime = os.environ.get('ERROR_IF_NOT_REALTIME')
        if not self.error_if_not_realtime:
            self.error_if_not_realtime = kwargs.get('error_if_not_realtime', False)
        
        self.processing_flag = False
        self.transcription_callback = transcription_callback

    def process_audio(self, vad_pipeline, asr_pipeline):
        """
        Process audio chunks by checking their length and scheduling asynchronous processing.

        This method checks if the length of the audio buffer exceeds the chunk length and, if so,
        it schedules asynchronous processing of the audio.

        Args:
            vad_pipeline: The voice activity detection pipeline.
            asr_pipeline: The automatic speech recognition pipeline.
        """
        chunk_length_in_bytes = int(self.chunk_length_seconds * self.client.sampling_rate) * self.client.samples_width
        if len(self.client.buffer) > chunk_length_in_bytes:
            if self.processing_flag:
                exit("Error in realtime processing: tried processing a new chunk while the previous one was still being processed")

            self.client.scratch_buffer += self.client.buffer
            self.client.buffer.clear()
            self.processing_flag = True
            # Schedule the processing in a separate task
            eventlet.spawn(self.process_audio_async, vad_pipeline, asr_pipeline)
    
    def process_audio_async(self, vad_pipeline, asr_pipeline):
        """
        Asynchronously process audio for activity detection and transcription.

        This method performs heavy processing, including voice activity detection and transcription of
        the audio data.

        Args:
            vad_pipeline: The voice activity detection pipeline.
            asr_pipeline: The automatic speech recognition pipeline.
        """
        start = time.time()
        vad_results = vad_pipeline.detect_activity(self.client)
        # first we will change segment times to be relative to the scratch buffer
        vad_results = [{'start': int(segment['start'] * self.client.sampling_rate) * self.client.samples_width,
                        'end': int(segment['end'] * self.client.sampling_rate) * self.client.samples_width} for segment
                       in vad_results]

        if len(vad_results) == 0:
            self.client.scratch_buffer.clear()
            self.client.buffer.clear()
            self.processing_flag = False
            return

        last_segment_should_end_before = len(self.client.scratch_buffer) - int(self.chunk_offset_seconds * self.client.sampling_rate) * self.client.samples_width
        if vad_results[-1]['end'] < last_segment_should_end_before:
            self.client.approved_segments = vad_results
            transcription = asr_pipeline.transcribe(self.client)
            if len(transcription["results"]) > 0:
                end = time.time()
                transcription['processing_time'] = end - start
                if self.client.transcription_callback:
                    print(f'Got {len(transcription["results"])} new transcription results')
                    print("sending transcription to callback")
                    self.client.transcription_callback(self.client.client_id, transcription)
            self.client.scratch_buffer.clear()
            self.client.increment_file_counter()
        self.processing_flag = False

class SilenceAnywhere(BufferingStrategyInterface):
    """
    A buffering strategy that processes audio at the end of each chunk with silence detection.

    This class is responsible for handling audio chunks, detecting silence at the end of each chunk,
    and initiating the transcription process for the chunk.

    Attributes:
        client (Client): The client instance associated with this buffering strategy.
        chunk_length_seconds (float): Length of each audio chunk in seconds.
        chunk_offset_seconds (float): quiet time in seconds to be considered for creating processable chunk.
    """

    def __init__(self, client, **kwargs):
        """
        Initialize the SilenceAtEndOfChunk buffering strategy.

        Args:
            client (Client): The client instance associated with this buffering strategy.
            **kwargs: Additional keyword arguments, including 'chunk_length_seconds' and 'chunk_offset_seconds'.
        """
        self.client = client

        self.chunk_length_seconds = os.environ.get('BUFFERING_CHUNK_LENGTH_SECONDS')
        if not self.chunk_length_seconds:
            self.chunk_length_seconds = kwargs.get('chunk_length_seconds')
        self.chunk_length_seconds = float(self.chunk_length_seconds)

        self.chunk_offset_seconds = os.environ.get('BUFFERING_CHUNK_OFFSET_SECONDS')
        if not self.chunk_offset_seconds:
            self.chunk_offset_seconds = kwargs.get('chunk_offset_seconds')
        self.chunk_offset_seconds = float(self.chunk_offset_seconds)

        self.error_if_not_realtime = os.environ.get('ERROR_IF_NOT_REALTIME')
        if not self.error_if_not_realtime:
            self.error_if_not_realtime = kwargs.get('error_if_not_realtime', False)

        self.processing_flag = False

    def process_audio(self, vad_pipeline, asr_pipeline):
        """
        Process audio chunks by checking their length and scheduling asynchronous processing.

        This method checks if the length of the audio buffer exceeds the chunk length and, if so,
        it schedules asynchronous processing of the audio.

        Args:
            vad_pipeline: The voice activity detection pipeline.
            asr_pipeline: The automatic speech recognition pipeline.
        """
        chunk_length_in_bytes = int(self.chunk_length_seconds * self.client.sampling_rate) * self.client.samples_width
        if len(self.client.buffer) > chunk_length_in_bytes:
            if self.processing_flag:
                exit(
                    "Error in realtime processing: tried processing a new chunk while the previous one was still being processed")

            self.client.scratch_buffer += self.client.buffer
            self.client.buffer.clear()
            self.processing_flag = True
            # Schedule the processing in a separate task
            eventlet.spawn(self.process_audio_async, vad_pipeline, asr_pipeline)

    def process_audio_async(self, vad_pipeline, asr_pipeline):
        """
        Asynchronously process audio for activity detection and transcription.

        This method performs heavy processing, including voice activity detection and transcription of
        the audio data.

        Args:
            vad_pipeline: The voice activity detection pipeline.
            asr_pipeline: The automatic speech recognition pipeline.
        """
        start = time.time()
        vad_results = vad_pipeline.detect_activity(self.client)
        if len(vad_results) == 0:
            self.client.scratch_buffer.clear()
            self.client.buffer.clear()
            self.processing_flag = False
            return
        # first we will change segment times to be relative to the scratch buffer
        vad_results = [{'start': int(segment['start'] * self.client.sampling_rate) * self.client.samples_width,
                        'end': int(segment['end'] * self.client.sampling_rate) * self.client.samples_width} for segment in vad_results]
        # This code segment return the end time of the latest segment that has at least chunk_offset_seconds of silence after it
        chunk_offset_samples = int (self.chunk_offset_seconds * self.client.sampling_rate) * self.client.samples_width
        i = 0
        for segment in reversed(vad_results):
            if i == 0 and (len(self.client.scratch_buffer) - segment['end'] >  chunk_offset_samples):
                break
            elif i > 0 and segment['start'] - vad_results[-i]['end'] > chunk_offset_samples:
                break
            i += 1
        split_segment = len(vad_results) - i

        self.client.approved_segments = vad_results[:split_segment]
        self.client.rejected_segments = vad_results[split_segment:]

        transcription = asr_pipeline.transcribe(self.client)
        print(f'Got {len(transcription["results"])} new transcription results')
        if len(transcription["results"]) > 0:
            print(f'Got {len(transcription["results"])} new transcription results')
            end = time.time()
            transcription['processing_time'] = end - start
            if len(self.client.approved_segments) > 0:
                last_approved_time = self.client.approved_segments[-1]['end']
                self.client.scratch_buffer = self.client.scratch_buffer[int(last_approved_time * self.client.sampling_rate) * self.client.samples_width:]
            if self.client.transcription_callback:
                self.client.transcription_callback(self.client.client_id, transcription)

        self.client.increment_file_counter()
        self.processing_flag = False