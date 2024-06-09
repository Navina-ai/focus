import json
from typing import Dict

import eventlet
import eventlet.wsgi
eventlet.monkey_patch()

import socketio
from src.client import Client
from src.config import DEFAULT_LANGUAGE, DEFAULT_PROCESSING_STRATEGY, DEFAULT_CHUNK_LENGTH_SECONDS, DEFAULT_CHUNK_OFFSET_SECONDS

class Server:
    def __init__(self, vad_pipeline, asr_pipeline, host='localhost', port=8765, sampling_rate=16000, samples_width=2, certfile=None, keyfile=None):
        self.vad_pipeline = vad_pipeline
        self.asr_pipeline = asr_pipeline
        self.host = host
        self.port = port
        self.sio = socketio.Server(cors_allowed_origins='*', async_mode='eventlet')
        self.app = socketio.WSGIApp(self.sio)
        self.certfile = certfile
        self.sampling_rate = sampling_rate
        self.samples_width = samples_width
        self.keyfile = keyfile
        self.connected_clients: Dict[str, Client] = {}

    def handle_config(self, client, message_json):
        client.update_config(message_json['data'])

    def send_transcription_result(self, sid, data):
        print("emiiting audioResponse")
        self.sio.emit('audioResponse', {'data': data}, to=sid)

    def start(self):
        @self.sio.event
        def connect(sid, environ):
            print(f"Client {sid} connected")
            client_id = sid
            client = Client(client_id, self.sampling_rate, self.samples_width, self.send_transcription_result)
            self.connected_clients[client_id] = client

        @self.sio.event
        def disconnect(sid):
            print(f"Client {sid} disconnected")
            client_to_remove = next((cid for cid, cl in self.connected_clients.items() if cl.client_id == sid), None)
            if client_to_remove:
                del self.connected_clients[client_to_remove]

        @self.sio.on('audioData')
        def handle_audio_data(sid, data):
            client = self.connected_clients.get(sid)
            if client:
                client.append_audio_data(data)
                client.process_audio(self.vad_pipeline, self.asr_pipeline)

        @self.sio.on('config')
        def handle_config(sid, config_message):
            client = next((cl for cl in self.connected_clients.values() if cl.client_id == sid), None)
            json_config = json.loads(config_message)
            json_config_data = json_config['data']
            if 'language' not in json_config_data:
                json_config_data['language'] = DEFAULT_LANGUAGE
            if 'processing_strategy' not in json_config_data:
                json_config_data['processing_strategy'] = DEFAULT_PROCESSING_STRATEGY
            if 'processing_args' not in json_config_data:
                json_config_data['processing_args'] = {
                    'chunk_length_seconds': DEFAULT_CHUNK_LENGTH_SECONDS,
                    'chunk_offset_seconds': DEFAULT_CHUNK_OFFSET_SECONDS
                }
            json_config['data'] = json_config_data
            if client:
                self.handle_config(client, json_config)

        if self.certfile and self.keyfile:
            ssl_context = (self.certfile, self.keyfile)
            eventlet.wsgi.server(eventlet.wrap_ssl(eventlet.listen((self.host, self.port)), certfile=self.certfile, keyfile=self.keyfile, server_side=True), self.app)
        else:
            eventlet.wsgi.server(eventlet.listen((self.host, self.port)), self.app)

        print(f"Server started on {self.host}:{self.port}")
