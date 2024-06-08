<template>
  <div>
    <div class="q-pa-md row justify-center">
      <div style="width: 100%; max-width: 400px">
        <q-chat-message
          :text="['hey, how are you?']"
          sent
        />
        <q-chat-message
          :text="['doing fine, how r you?']"
        />
      </div>
    </div>
    <p>{{ title }}</p>
    <ul>
      <li v-for="todo in todos" :key="todo.id" @click="increment">
        {{ todo.id }} - {{ todo.content }}
      </li>
    </ul>
    <p>Count: {{ todoCount }} / {{ meta.totalCount }}</p>
    <p>Active: {{ active ? 'yes' : 'no' }}</p>
    <p>Clicks on todos: {{ clickCount }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import {QChatMessage} from 'quasar';
import { Todo, Meta } from './models';

interface Props {
  title: string;
  todos?: Todo[];
  meta: Meta;
  active: boolean;
};

const props = withDefaults(defineProps<Props>(), {
  todos: () => []
});

const clickCount = ref(0);
function increment() {
  clickCount.value += 1;
  return clickCount.value;
}

const todoCount = computed(() => props.todos.length);
</script>
