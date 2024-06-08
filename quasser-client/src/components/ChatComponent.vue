<template>
  <div class="chat-display">
    <div v-for="segment in chatStore.segments" :key="segment.text">
      <span :style="{ color: getColor(segment.speaker) }">
        {{ segment.text }} <span v-if="!segment.is_finalized">(typing...)</span>
      </span>
    </div>
  </div>
</template>

<script setup>
import { useChatStore } from '../stores/useChatStore';

const { chatStore } = useChatStore();

const getColor = (speaker) => {
  const colors = ['blue', 'red', 'green', 'purple'];
  return colors[speaker % colors.length];
};
</script>

<style scoped>
.chat-display {
  max-height: 400px;
  overflow-y: scroll;
  padding: 10px;
  background-color: #f4f4f4;
  border-radius: 10px;
}
</style>
