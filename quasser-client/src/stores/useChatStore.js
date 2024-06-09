import { reactive } from 'vue';

const chatStore = reactive({
    segments: []
});

export function useChatStore() {
    const addMessages = (messages) => {
        const newSegments = messages.results;
        if (newSegments.length > 0) {
          // Remove the last non-finalized segment
          clearNonFinalized();
          chatStore.segments.push(...newSegments);
        }
        // Add new segments
    };

    const clearNonFinalized = () => {
      // Clear non-finalized segments from the display
      while (chatStore.segments.length > 0 && !chatStore.segments[chatStore.segments.length - 1].is_finalized) {
        chatStore.segments.pop();
      }
    };

    return { chatStore, addMessages, clearNonFinalized };
}
