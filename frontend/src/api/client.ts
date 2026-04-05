import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { Token } from '@/types'

// Module-level token variable - avoids circular dependency with auth store.
// Auth store calls setAccessToken() after login/refresh.
let _accessToken: string | null = null

export function setAccessToken(token: string | null): void {
  _accessToken = token
}

export function getAccessToken(): string | null {
  return _accessToken
}

export const apiClient = axios.create({
  withCredentials: true, // sends the httponly refresh_token cookie
})

// ── Request interceptor: attach Bearer token ──────────────────────────────
apiClient.interceptors.request.use((config) => {
  if (_accessToken) {
    config.headers.Authorization = `Bearer ${_accessToken}`
  }
  return config
})

// ── Response interceptor: handle 401 + auto-refresh ──────────────────────
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null = null): void {
  for (const p of failedQueue) {
    if (error) p.reject(error)
    else p.resolve(token!)
  }
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Only handle 401 on non-auth endpoints and non-retried requests
    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes('/v1/auth/')
    ) {
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          original.headers.Authorization = `Bearer ${token}`
          return apiClient(original)
        })
      }

      original._retry = true
      isRefreshing = true

      try {
        const { data } = await apiClient.post<Token>('/v1/auth/refresh')
        const newToken = data.access_token
        setAccessToken(newToken)
        processQueue(null, newToken)
        original.headers.Authorization = `Bearer ${newToken}`
        return apiClient(original)
      } catch (refreshError) {
        processQueue(refreshError, null)
        // Lazy import to avoid circular dep
        const { useAuthStore } = await import('@/stores/auth')
        useAuthStore().clearSession()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)
