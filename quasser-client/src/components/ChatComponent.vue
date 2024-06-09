<template>
  <div class="chat-display">
    <div v-for="group in groupedSegments" :key="group[0].key">
      <span v-for="segment in group" :key="segment.text" :style="{ color: getColor(segment.speaker), opacity: segment.is_finalized ? '1' : '0.5', animation: !segment.is_finalized ? 'blink 1s linear infinite' : 'none' }">
        {{ segment.text }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useChatStore } from '../stores/useChatStore';

const { chatStore } = useChatStore();

const groupedSegments = computed(() => {
  const groups = [];
  let group_key = 0;
  let currentGroup = [];

  chatStore.segments.forEach((segment, index) => {
    let segment_key = 0;
    if (currentGroup.length === 0 || currentGroup[0].speaker === segment.speaker) {
      // segment_key is concat of group_key and segment_key
      segment.key = `${group_key}-${segment_key}`;
      currentGroup.push(segment);
      segment_key++;
    } else {
      groups.push(currentGroup);
      group_key++;
      currentGroup = [segment];
    }
    // Check if last item
    if (index === chatStore.segments.length - 1) {
      groups.push(currentGroup);
    }
  });

  return groups;
});

const getColor = (speaker) => {
  const colors = ['blue', 'red', 'green', 'purple'];
  if (speaker === -1) {
    return 'gray';
  }
  return colors[speaker % colors.length];
};
</script>

<style>
.chat-display {
  max-height: 400px;
  overflow-y: scroll;
  padding: 10px;
  background-color: #f4f4f4;
  border-radius: 10px;
}

@keyframes blink {
  0%, 100% { opacity: 0.1; }
  50% { opacity: 0.7; }
}

.chat-display {
  max-height: 400px;
  overflow-y: scroll;
  padding: 10px;
  background-color: #f4f4f4;
  border-radius: 10px;
}

</style>
