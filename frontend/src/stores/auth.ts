import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setAccessToken } from '@/api/client'
import { authApi } from '@/api/auth'
import { usersApi } from '@/api/users'
import type { UserOut, Token, TenantOut } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserOut | null>(null)
  const accessToken = ref<string | null>(null)
  const permissions = ref<string[]>([])
  const tenants = ref<TenantOut[]>([])
  const isInitialized = ref(false)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)

  function hasPermission(permission: string): boolean {
    return permissions.value.includes(permission)
  }

  function setSession(token: Token): void {
    accessToken.value = token.access_token
    setAccessToken(token.access_token)
    localStorage.setItem('access_token', token.access_token)
  }

  function clearSession(): void {
    user.value = null
    accessToken.value = null
    permissions.value = []
    tenants.value = []
    setAccessToken(null)
    localStorage.removeItem('access_token')
  }

  async function fetchMe(): Promise<void> {
    const { data } = await usersApi.getMe()
    user.value = data
    permissions.value = [...new Set(data.roles.flatMap((r) => r.permissions.map((p) => p.name)))]
  }

  async function fetchTenants(): Promise<void> {
    const { data } = await usersApi.getMyTenants()
    tenants.value = data
  }

  async function initialize(): Promise<void> {
    const storedToken = localStorage.getItem('access_token')
    if (storedToken) {
      accessToken.value = storedToken
      setAccessToken(storedToken)
      try {
        await Promise.all([fetchMe(), fetchTenants()])
      } catch {
        clearSession()
      }
    }
    isInitialized.value = true
  }

  async function login(email: string, password: string): Promise<void> {
    const { data: token } = await authApi.login(email, password)
    setSession(token)
    await Promise.all([fetchMe(), fetchTenants()])
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch {
      // ignore
    }
    clearSession()
  }

  async function switchTenant(tenantId: number): Promise<void> {
    const { data: token } = await authApi.switchTenant({ tenant_id: tenantId })
    setSession(token)
    await fetchMe()
  }

  return {
    user,
    accessToken,
    permissions,
    tenants,
    isInitialized,
    isAuthenticated,
    hasPermission,
    setSession,
    clearSession,
    fetchMe,
    fetchTenants,
    initialize,
    login,
    logout,
    switchTenant,
  }
})
