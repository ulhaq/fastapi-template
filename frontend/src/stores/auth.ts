import { defineStore } from 'pinia'
import { computed } from 'vue'
import { authApi } from '@/api/auth'
import { useSessionStore } from '@/stores/session'
import { useProfileStore } from '@/stores/profile'
import { useTenancyStore } from '@/stores/tenancy'
import { useSubscriptionStore } from '@/stores/subscription'
import type { Token } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const session = useSessionStore()
  const profile = useProfileStore()
  const tenancy = useTenancyStore()
  const subscription = useSubscriptionStore()

  const isInitialized = computed(() => session.isInitialized)
  const isAuthenticated = computed(() => session.isAuthenticated)
  const hasActiveSubscription = computed(() => subscription.hasActiveSubscription)

  function setSession(token: Token): void {
    session.setToken(token.access_token)
  }

  function clearSession(): void {
    session.clear()
    profile.clear()
    tenancy.clear()
    subscription.clear()
  }

  async function initialize(): Promise<void> {
    try {
      const { data: token } = await authApi.refresh()
      session.setToken(token.access_token)
      await Promise.all([profile.fetchMe(), tenancy.fetchTenants(), subscription.fetchSubscriptionStatus()])
    } catch {
      // No valid session cookie - proceed as unauthenticated.
    }
    session.isInitialized = true
  }

  async function login(email: string, password: string): Promise<void> {
    const { data: token } = await authApi.login(email, password)
    setSession(token)
    await Promise.all([profile.fetchMe(), tenancy.fetchTenants(), subscription.fetchSubscriptionStatus()])
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
    await Promise.all([profile.fetchMe(), tenancy.fetchTenants(), subscription.fetchSubscriptionStatus()])
  }

  async function switchTenant(tenantId: number): Promise<void> {
    const { data: token } = await authApi.switchTenant({ tenant_id: tenantId })
    setSession(token)
    await Promise.all([profile.fetchMe(), subscription.fetchSubscriptionStatus()])
    // tenants list does not change on switch
  }

  return {
    isInitialized,
    isAuthenticated,
    hasActiveSubscription,
    setSession,
    clearSession,
    initialize,
    login,
    logout,
    completeRegistration,
    switchTenant,
  }
})
