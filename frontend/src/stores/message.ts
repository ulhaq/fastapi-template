import type { Message } from '@/types/message'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useMessageStore = defineStore('message', () => {
  const queue = ref<Message[]>([])

  function add (message: Message) {
    const msg = {
      ...message,
      timeout: message.timeout ?? 3000,
    }
    queue.value.push(msg)

    setTimeout(() => {
      const index = queue.value.indexOf(msg)
      if (index !== -1) {
        queue.value.splice(index, 1)
      }
    }, msg.timeout)
  }

  return { queue, add }
})
