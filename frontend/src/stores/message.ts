import { defineStore } from "pinia";

export const useMessageStore = defineStore("message", () => {
  const queue = ref([]);

  function add(message) {
    queue.value.push(message);
  }

  return { queue, add };
});
