import { reactive } from 'vue';

const chatStore = reactive({
    segments: []
});

export function useChatStore() {
    const addMessage = (message) => {
        const newSegments = message.results;
        if (newSegments.length > 0 && !newSegments[0].is_finalized) {
            // Remove the last non-finalized segment
            if (chatStore.segments.length > 0 && !chatStore.segments[chatStore.segments.length - 1].is_finalized) {
                chatStore.segments.pop();
            }
        }
        // Add new segments
        chatStore.segments.push(...newSegments.filter(segment => segment.is_finalized));
    };

    const clearNonFinalized = () => {
        if (chatStore.segments.length > 0 && !chatStore.segments[chatStore.segments.length - 1].is_finalized) {
            chatStore.segments.pop();
        }
    };

    return { chatStore, addMessage, clearNonFinalized };
}
