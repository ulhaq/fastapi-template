import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setAccessToken } from '@/api/client'

export const useSessionStore = defineStore('session', () => {
  const accessToken = ref<string | null>(null)
  const isInitialized = ref(false)
  const isAuthenticated = computed(() => !!accessToken.value)

  function setToken(token: string | null): void {
    accessToken.value = token
    setAccessToken(token)
  }

  function clear(): void {
    accessToken.value = null
    setAccessToken(null)
  }

  return { accessToken, isInitialized, isAuthenticated, setToken, clear }
})
