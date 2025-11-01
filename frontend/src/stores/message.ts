import type { Message } from '@/types/message'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useMessageStore = defineStore('message', () => {
  const queue = ref<Message[]>([])

  function add (message: Message) {
    const msg = {
      ...message,
      timeout: message.timeout ?? 5000,
    }

    if (!exists(msg) || msg.type === 'success') {
      queue.value = [...queue.value, msg]
    }

    if (msg.timeout > 0) {
      setTimeout(() => remove(msg), msg.timeout)
    }
  }

  function remove (message: Message) {
    queue.value = queue.value.filter(msg => msg.text !== message.text)
  }

  function clear () {
    queue.value = []
  }

  function clearErrors () {
    queue.value = queue.value.filter(msg => msg.type != 'error')
  }

  function exists (message: Message) {
    return queue.value.some(msg => msg.text === message.text)
  }

  return { queue, add, clear, clearErrors, remove }
})
