import argparse
import json

import eventlet
eventlet.monkey_patch()
from server import Server
from src.asr.asr_factory import ASRFactory
from src.vad.vad_factory import VADFactory
from src.spr.spr_factory import SPRFactory
from src.config import VAD_AUTH_TOKEN, PORT, HOST

def parse_args():
    parser = argparse.ArgumentParser(description="VoiceStreamAI Server: Real-time audio transcription using self-hosted Whisper and WebSocket")
    parser.add_argument("--vad-type", type=str, default="pyannote", help="Type of VAD pipeline to use (e.g., 'pyannote')")
    parser.add_argument("--vad-args", type=str, default=f'{{"auth_token": "{VAD_AUTH_TOKEN}"}}', help="JSON string of additional arguments for VAD pipeline")
    parser.add_argument("--asr-type", type=str, default="faster_whisper", help="Type of ASR pipeline to use (e.g., 'whisper')")
    parser.add_argument("--asr-args", type=str, default='{"model_size": "large-v3"}', help="JSON string of additional arguments for ASR pipeline")
    parser.add_argument("--host", type=str, default=HOST, help="Host for the WebSocket server")
    parser.add_argument("--port", type=int, default=PORT, help="Port for the WebSocket server")
    parser.add_argument("--certfile", type=str, default=None, help="The path to the SSL certificate (cert file) if using secure websockets")
    parser.add_argument("--keyfile", type=str, default=None, help="The path to the SSL key file if using secure websockets")
    return parser.parse_args()

def main():
    args = parse_args()

    try:
        vad_args = json.loads(args.vad_args)
        asr_args = json.loads(args.asr_args)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON arguments: {e}")
        return

    vad_pipeline = VADFactory.create_vad_pipeline(args.vad_type, **vad_args)
    spr_pipeline = SPRFactory.create_spr_pipeline('pyannote')
    asr_pipeline = ASRFactory.create_asr_pipeline(args.asr_type, spr_pipeline, **asr_args)

    server = Server(vad_pipeline, asr_pipeline, host=args.host, port=args.port, sampling_rate=16000, samples_width=2, certfile=args.certfile, keyfile=args.keyfile)

    server.start()
    eventlet.wsgi.server(eventlet.listen(('', 8000)), server.app)

if __name__ == "__main__":
    main()
