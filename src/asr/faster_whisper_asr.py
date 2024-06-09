from itertools import chain
from faster_whisper import WhisperModel

from .asr_interface import ASRInterface
from src.spr.spr_interface import SPRInterface
from src.audio_utils import save_audio_to_file, bytearray_audio_to_nparray

language_codes = {
    "afrikaans": "af",
    "amharic": "am",
    "arabic": "ar",
    "assamese": "as",
    "azerbaijani": "az",
    "bashkir": "ba",
    "belarusian": "be",
    "bulgarian": "bg",
    "bengali": "bn",
    "tibetan": "bo",
    "breton": "br",
    "bosnian": "bs",
    "catalan": "ca",
    "czech": "cs",
    "welsh": "cy",
    "danish": "da",
    "german": "de",
    "greek": "el",
    "english": "en",
    "spanish": "es",
    "estonian": "et",
    "basque": "eu",
    "persian": "fa",
    "finnish": "fi",
    "faroese": "fo",
    "french": "fr",
    "galician": "gl",
    "gujarati": "gu",
    "hausa": "ha",
    "hawaiian": "haw",
    "hebrew": "he",
    "hindi": "hi",
    "croatian": "hr",
    "haitian": "ht",
    "hungarian": "hu",
    "armenian": "hy",
    "indonesian": "id",
    "icelandic": "is",
    "italian": "it",
    "japanese": "ja",
    "javanese": "jw",
    "georgian": "ka",
    "kazakh": "kk",
    "khmer": "km",
    "kannada": "kn",
    "korean": "ko",
    "latin": "la",
    "luxembourgish": "lb",
    "lingala": "ln",
    "lao": "lo",
    "lithuanian": "lt",
    "latvian": "lv",
    "malagasy": "mg",
    "maori": "mi",
    "macedonian": "mk",
    "malayalam": "ml",
    "mongolian": "mn",
    "marathi": "mr",
    "malay": "ms",
    "maltese": "mt",
    "burmese": "my",
    "nepali": "ne",
    "dutch": "nl",
    "norwegian nynorsk": "nn",
    "norwegian": "no",
    "occitan": "oc",
    "punjabi": "pa",
    "polish": "pl",
    "pashto": "ps",
    "portuguese": "pt",
    "romanian": "ro",
    "russian": "ru",
    "sanskrit": "sa",
    "sindhi": "sd",
    "sinhalese": "si",
    "slovak": "sk",
    "slovenian": "sl",
    "shona": "sn",
    "somali": "so",
    "albanian": "sq",
    "serbian": "sr",
    "sundanese": "su",
    "swedish": "sv",
    "swahili": "sw",
    "tamil": "ta",
    "telugu": "te",
    "tajik": "tg",
    "thai": "th",
    "turkmen": "tk",
    "tagalog": "tl",
    "turkish": "tr",
    "tatar": "tt",
    "ukrainian": "uk",
    "urdu": "ur",
    "uzbek": "uz",
    "vietnamese": "vi",
    "yiddish": "yi",
    "yoruba": "yo",
    "chinese": "zh",
    "cantonese": "yue",
}


class FasterWhisperASR(ASRInterface):
    def __init__(self, spr_pipeline: SPRInterface, **kwargs):
        model_size = kwargs.get('model_size', "large-v3")
        # Run on GPU with FP16
        self.asr_pipeline = WhisperModel(model_size, device="cuda", compute_type="float16")
        self.spr_pipeline = spr_pipeline
    def transcribe(self, client):
        spr_sample_rate = self.spr_pipeline.model.hparams.get('sample_rate', 16000)
        # first we will run spr_pipeline on each segment
        for segment in client.approved_segments + client.rejected_segments:
                audio_np = bytearray_audio_to_nparray(client.scratch_buffer[segment['start']:segment['end']], spr_sample_rate)
                speaker = self.spr_pipeline.classify_speaker(client.client_id, audio_np)
                segment['speaker'] = speaker

        # we want to change every unknown speaker (-1) to the last known speaker and concat into larger segments accordingly
        last_known_speaker = client.last_speaker

        def merge_segments_by_speaker(list_segments):
            new_segments = []
            current_open_speaker = None
            for cur_segment in list_segments:
                if cur_segment['speaker'] == -1:
                    cur_segment['speaker'] = last_known_speaker
                client.last_speaker = cur_segment['speaker']
                if current_open_speaker is None:
                    current_open_speaker = cur_segment['speaker']
                    new_segments.append(cur_segment)
                else:
                    if cur_segment['speaker'] == current_open_speaker:
                        new_segments[-1]['end'] = cur_segment['end']
                    else:
                        current_open_speaker = cur_segment['speaker']
                        new_segments.append(cur_segment)
            return new_segments

        new_approved_segments = merge_segments_by_speaker(client.approved_segments)
        new_rejected_segments = merge_segments_by_speaker(client.rejected_segments)
        print (f"about to transcript {len(new_approved_segments)} approved segments and {len(new_rejected_segments)} rejected segments")
        # now we will transcribe each segment
        language = None if client.config['language'] is None else language_codes.get(client.config['language'].lower())
        transcription = {"results": []}
        # Create iterators for approved and rejected segments with True/False flags
        approved = zip(new_approved_segments, [True] * len(new_approved_segments))
        rejected = zip(new_rejected_segments, [False] * len(new_rejected_segments))

        # Chain them together to iterate over all segments
        all_segments = chain(approved, rejected)
        for segment, is_finalized in all_segments:
            print (f"transcripting segment {segment['start']} to {segment['end']}")
            audio_np = bytearray_audio_to_nparray(client.scratch_buffer[segment['start']:segment['end']], client.sampling_rate)
            segments, info = self.asr_pipeline.transcribe(audio_np, word_timestamps=True, language=language)
            segments = list(segments)  # The transcription will actually run here.

            flattened_words = [word for segment in segments for word in segment.words]

            segment_transcribe = {
            "language": info.language,
            "language_probability": info.language_probability,
            "text": ' '.join([s.text.strip() for s in segments]),
            "speaker": segment['speaker'],
            "words":
                [
                    {"word": w.word, "start": w.start, "end": w.end, "probability":w.probability} for w in flattened_words
                ],
            "is_finalized": is_finalized
            }
            print(f"transcription results: {segment_transcribe['text']}")
            transcription["results"].append(segment_transcribe)

        return transcription

