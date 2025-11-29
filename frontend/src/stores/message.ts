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

    return Math.max(totalMs, 7000)
  }

  const queue = ref<Message[]>([])

  function add(message: Omit<Message, 'time'>) {
    const msg = {
      ...message,
      time: Date.now(),
      timeout: message.timeout ?? (calculateReadingTime(message.text) || 5000),
    }

    const messageIndex = indexOf(msg)
    if (messageIndex >= 0 && msg.type !== 'success') {
      queue.value.splice(messageIndex, 1)
    }
    queue.value = [msg, ...queue.value]

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

  function indexOf(message: Message) {
    return queue.value.findIndex(
      (msg) =>
        msg.text === message.text &&
        msg.type === message.type &&
        msg.timeout === message.timeout,
    )
  }

  return { queue, add, clear, clearErrors, remove }
})
