import { ref } from 'vue';
import { sendMessage, websocket } from './websocket';

const isRecording = ref(false);
let audioContext = null;
let processor = null;
let globalStream = null;

const bufferSize = 4096;

export function useAudioRecorder() {
    const startRecording = () => {
        if (isRecording.value) return;
        isRecording.value = true;

        const AudioContext = window.AudioContext || window.webkitAudioContext;
        audioContext = new AudioContext();

        navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
            globalStream = stream;
            const input = audioContext.createMediaStreamSource(stream);
            processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
            processor.onaudioprocess = processAudio;
            input.connect(processor);
            processor.connect(audioContext.destination);

            sendAudioConfig();
        }).catch(error => console.error('Error accessing microphone', error));
    };

    const stopRecording = () => {
        if (!isRecording.value) return;
        isRecording.value = false;

        if (globalStream) {
            globalStream.getTracks().forEach(track => track.stop());
        }
        if (processor) {
            processor.disconnect();
            processor = null;
        }
        if (audioContext) {
            audioContext.close().then(() => audioContext = null);
        }
    };

    const sendAudioConfig = () => {
        const audioConfig = {
            type: 'config',
            data: {
                sampleRate: audioContext.sampleRate,
                bufferSize: bufferSize,
                channels: 1, // Assuming mono channel
            }
        };
        sendMessage(JSON.stringify(audioConfig));
    };

    const processAudio = (e) => {
        const inputBuffer = e.inputBuffer.getChannelData(0);
        const outputSampleRate = 16000; // Target sample rate
        const downsampledBuffer = downsampleBuffer(inputBuffer, audioContext.sampleRate, outputSampleRate);
        const audioData = convertFloat32ToInt16(downsampledBuffer);
        if (websocket.value && websocket.value.readyState === WebSocket.OPEN) {
          websocket.value.send(audioData);
        }
    };

    const downsampleBuffer = (buffer, inputSampleRate, outputSampleRate) => {
    if (inputSampleRate === outputSampleRate) {
        return buffer;
    }
    const sampleRateRatio = inputSampleRate / outputSampleRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
        const start = Math.floor(i * sampleRateRatio);
        const end = Math.floor((i + 1) * sampleRateRatio);

        let accum = 0;
        for (let j = start; j < end && j < buffer.length; j++) {
            accum += buffer[j];
        }

        // Avoid division by zero by ensuring there's at least one element to average
        const count = end - start;
        result[i] = count > 0 ? accum / count : 0; // Protect against division by zero
    }

    return result;
};


    const convertFloat32ToInt16 = (buffer) => {
        let l = buffer.length;
        const buf = new Int16Array(l);
        while (l--) {
            buf[l] = Math.min(1, buffer[l]) * 0x7FFF;
        }
        return buf.buffer;
    };

    return { startRecording, stopRecording, isRecording };
}
