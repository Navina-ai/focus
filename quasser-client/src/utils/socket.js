// This module will manage the Socket.IO client

import { io } from 'socket.io-client';
import { useChatStore } from '../stores/useChatStore';

const { addMessages } = useChatStore();

const socket = io('http://10.0.2.155:8000');

socket.on('connect', () => {
    console.log('Connected to server via Socket.IO');
});

socket.on('audioResponse', (message) => {
    console.log('Received message:', message);
    addMessages(message.data);
});

export function sendAudio(data) {
    socket.emit('audioData', data);
}
export function sendConfig(data) {
    socket.emit('config', data);
}
export function closeConnection() {
    socket.close();
}

export default socket;
