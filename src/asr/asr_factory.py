from .whisper_asr import WhisperASR
from .faster_whisper_asr import FasterWhisperASR
from src.spr.spr_interface import SPRInterface
class ASRFactory:
    @staticmethod
    def create_asr_pipeline(type, spr_pipeline: SPRInterface ,**kwargs):
        if type == "whisper":
            return WhisperASR(spr_pipeline, **kwargs)
        if type == "faster_whisper":
            return FasterWhisperASR(spr_pipeline, **kwargs)
        else:
            raise ValueError(f"Unknown ASR pipeline type: {type}")
