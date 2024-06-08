<template>
  <q-page>
    <chat-component />
    <q-btn :disabled="isRecording" label="Start Recording" @click="startRecording" />
    <q-btn :disabled="!isRecording" label="Stop Recording" @click="stopRecording" />
  </q-page>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { useAudioRecorder } from '../utils/audioProcessing';
import { initWebSocket, closeWebSocket } from '../utils/websocket';
import ChatComponent from '../components/ChatComponent.vue';

const { startRecording, stopRecording, isRecording } = useAudioRecorder();

onMounted(() => {
  initWebSocket('ws://10.0.2.155:8000');
});

onUnmounted(() => {
  closeWebSocket();
});
</script>
