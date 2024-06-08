import { ref } from 'vue';
import { useChatStore } from '../stores/useChatStore'; // Import your chat store

export const websocket = ref(null);

export function initWebSocket(address) {
  if (!address) {
    console.error('WebSocket address is required.');
    return;
  }
  const { addMessage } = useChatStore(); // Use the chat store

  websocket.value = new WebSocket(address);
  websocket.value.onopen = () => console.log('WebSocket connection established');
  websocket.value.onclose = event => console.log('WebSocket connection closed', event);
  websocket.value.onmessage = event => {
    console.log('Message from server:', event.data);
    const data = JSON.parse(event.data);
    addMessage(data); // Update the chat store with new message
  };
}

export function sendMessage(message) {
  if (websocket.value && websocket.value.readyState === WebSocket.OPEN) {
    websocket.value.send(message);
  }
}

export function closeWebSocket() {
  if (websocket.value) {
    websocket.value.close();
  }
}
