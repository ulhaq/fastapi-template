import { defineStore } from "pinia";

export const useMessageStore = defineStore("messages", () => {
  const queue = ref([]);

  function add(message) {
    queue.value.push(message);
  }

  return { queue, add };
});
