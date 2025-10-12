import type { Message } from '@/types/message'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useMessageStore = defineStore('message', () => {
  const queue = ref<Message[]>([])

  function add (message: Message) {
    queue.value.push({
      ...message,
      timeout: message.timeout ?? 3000,
    })
  }

  return { queue, add }
})
