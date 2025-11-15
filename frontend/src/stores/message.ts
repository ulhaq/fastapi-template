import type { Message } from '@/types/message'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useMessageStore = defineStore('message', () => {
  function calculateReadingTime(
    text: string,
    lettersPerSecond: number = 7,
  ): number {
    if (!text?.trim()) return 0

    const letterCount = text.replaceAll(' ', '').length
    const totalMs = Math.ceil((letterCount / lettersPerSecond) * 1000)

    return totalMs
  }

  const queue = ref<Message[]>([])

  function add(message: Omit<Message, 'time'>) {
    const msg = {
      ...message,
      time: Date.now(),
      timeout: message.timeout ?? (calculateReadingTime(message.text) || 5000),
    }

    if (!exists(msg) || msg.type === 'success') {
      queue.value = [msg, ...queue.value]
    }

    if (msg.timeout > 0) {
      setTimeout(() => remove(msg), msg.timeout)
    }
  }

  function remove(message: Message) {
    queue.value = queue.value.filter(
      (msg) => msg.time !== message.time || msg.text !== message.text,
    )
  }

  function clear() {
    queue.value = []
  }

  function clearErrors() {
    queue.value = queue.value.filter((msg) => msg.type != 'error')
  }

  function exists(message: Message) {
    return queue.value.some((msg) => msg.text === message.text)
  }

  return { queue, add, clear, clearErrors, remove }
})
