<template>
  <q-page>
    <ChatComponent />
    <q-btn :disabled="isRecording" label="Start Recording" @click="startRecording" />
    <q-btn :disabled="!isRecording" label="Stop Recording" @click="stopRecording" />
  </q-page>
</template>

<script setup>
import {onUnmounted} from 'vue';
import {useAudioRecorder} from '../utils/audioProcessing';
import {closeConnection} from '../utils/socket';
import ChatComponent from '../components/ChatComponent.vue';

const {startRecording, stopRecording, isRecording} = useAudioRecorder();

onUnmounted(() => {
  closeConnection()
});
</script>
