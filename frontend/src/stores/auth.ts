import type { User } from '@/types/user'
import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import authApi from '@/apis/auth'
import axios from '@/apis/base'

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter()

  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const loading = ref(true)

  const isAuthenticated = computed(() => !!accessToken.value)

  watch(accessToken, token => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  })

  function setAccessToken (token: string) {
    accessToken.value = token
  }

  function unsetAccessToken () {
    accessToken.value = null
  }

  async function login (email: string, password: string) {
    loading.value = true
    try {
      const res = await authApi.getToken(email, password)
      setAccessToken(res.access_token)
      await setUser()
    } finally {
      loading.value = false
    }
  }

  async function refreshToken () {
    loading.value = true
    try {
      const res = await authApi.refreshToken()
      setAccessToken(res.access_token)
      await setUser()
      return res.access_token
    } finally {
      loading.value = false
    }
  }

  async function requestPasswordReset (email: string) {
    loading.value = true
    try {
      return await authApi.requestPasswordReset(email)
    } finally {
      loading.value = false
    }
  }

  async function resetPassword (password: string, token: string) {
    loading.value = true
    try {
      return await authApi.resetPassword(password, token)
    } finally {
      loading.value = false
    }
  }

  async function logout () {
    await authApi.logout()
    unsetAccessToken()
    user.value = null
    router.push({ name: 'login' })
  }

  async function register (name: string, email: string, password: string) {
    loading.value = true
    try {
      return await authApi.register(name, email, password)
    } finally {
      loading.value = false
    }
  }

  async function setUser () {
    user.value = await authApi.getAuthenticatedUser()
  }

  async function getUser () {
    return user.value
  }

  return {
    user,
    accessToken,
    loading,
    isAuthenticated,
    login,
    refreshToken,
    requestPasswordReset,
    resetPassword,
    logout,
    register,
    getUser,
  }
})
