import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const apiUrl = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`

if (!import.meta.env.VITE_API_URL) {
  console.warn('No VITE_API_URL found, using fallback URL:', apiUrl)
}

const apiClient: AxiosInstance = axios.create({
  baseURL: apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

let requestQueue: Array<(token: string) => void> = []

function queueFailedRequest (callback: (token: string) => void) {
  requestQueue.push(callback)
}

function resolveFailedRequests (token: string) {
  for (const cb of requestQueue) {
    cb(token)
  }
  requestQueue = []
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const authStore = useAuthStore()

  if (authStore.accessToken && config.headers) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`
  }

  return config
})

apiClient.interceptors.response.use(
  response => response,
  async (error: AxiosError) => {
    const authStore = useAuthStore()
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    if (error.response?.status !== 401 || originalRequest._retry) {
      throw error
    }

    originalRequest._retry = true

    if (authStore.loading) {
      throw error
    }

    if (authStore.loading) {
      return new Promise(resolve => {
        queueFailedRequest((newToken: string) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
          }
          resolve(apiClient(originalRequest))
        })
      })
    }

    try {
      authStore.loading = true

      const newToken = await authStore.refreshToken()

      resolveFailedRequests(newToken)

      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`
      }

      return apiClient(originalRequest)
    } catch (refreshError) {
      await authStore.logout()
      throw refreshError instanceof Error ? refreshError : new Error(String(refreshError))
    } finally {
      authStore.loading = false
    }
  },
)

export default apiClient
