import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import { setAccessToken } from '@/api/client'
import { authApi } from '@/api/auth'
import { billingApi } from '@/api/billing'
import { usersApi } from '@/api/users'
import type { UserOut, Token, TenantOut } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserOut | null>(null)
  const accessToken = ref<string | null>(null)
  const permissions = ref<string[]>([])
  const tenants = ref<TenantOut[]>([])
  const isInitialized = ref(false)
  const subscriptionStatus = ref<string | null>(null)
  const subscriptionTrialEnd = ref<string | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const hasActiveSubscription = computed(() =>
    subscriptionStatus.value === 'active' || subscriptionStatus.value === 'trialing',
  )

  function hasPermission(permission: string): boolean {
    return permissions.value.includes(permission)
  }

  function setSession(token: Token): void {
    accessToken.value = token.access_token
    setAccessToken(token.access_token)
  }

  function clearSession(): void {
    user.value = null
    accessToken.value = null
    permissions.value = []
    tenants.value = []
    subscriptionStatus.value = null
    subscriptionTrialEnd.value = null
    setAccessToken(null)
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

  async function fetchSubscriptionStatus(): Promise<void> {
    try {
      const { data } = await billingApi.getCurrentSubscription()
      subscriptionStatus.value = data.status
      subscriptionTrialEnd.value = data.trial_end
    } catch {
      subscriptionStatus.value = null
      subscriptionTrialEnd.value = null
    }
  }

  async function initialize(): Promise<void> {
    try {
      // Restore session from the httponly refresh-token cookie (silent refresh).
      const { data: token } = await authApi.refresh()
      accessToken.value = token.access_token
      setAccessToken(token.access_token)
      await Promise.all([fetchMe(), fetchTenants(), fetchSubscriptionStatus()])
    } catch {
      // No valid session cookie - proceed as unauthenticated.
    }
    isInitialized.value = true
  }

  async function login(email: string, password: string): Promise<void> {
    const { data: token } = await authApi.login(email, password)
    setSession(token)
    await Promise.all([fetchMe(), fetchTenants(), fetchSubscriptionStatus()])
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch {
      // ignore
    }
    clearSession()
  }

  async function completeRegistration(setupToken: string, name: string, password: string): Promise<void> {
    const { data: token } = await authApi.completeRegistration({
      setup_token: setupToken,
      name,
      password,
    })
    setSession(token)
    await Promise.all([fetchMe(), fetchTenants(), fetchSubscriptionStatus()])
  }

  async function switchTenant(tenantId: number): Promise<void> {
    const { data: token } = await authApi.switchTenant({ tenant_id: tenantId })
    setSession(token)
    await Promise.all([fetchMe(), fetchSubscriptionStatus()])
  }

  return {
    user,
    accessToken,
    permissions,
    tenants,
    subscriptionStatus,
    subscriptionTrialEnd,
    isInitialized,
    isAuthenticated,
    hasActiveSubscription,
    hasPermission,
    setSession,
    clearSession,
    fetchMe,
    fetchTenants,
    fetchSubscriptionStatus,
    initialize,
    login,
    logout,
    completeRegistration,
    switchTenant,
  }
})
