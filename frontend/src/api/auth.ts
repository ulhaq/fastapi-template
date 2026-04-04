import { apiClient } from './client'
import type { Token, ResetPasswordRequestIn, ResetPasswordIn, SwitchTenantIn } from '@/types'

export const authApi = {
  login(email: string, password: string) {
    const form = new URLSearchParams()
    form.append('username', email) // OAuth2 spec uses 'username'
    form.append('password', password)
    return apiClient.post<Token>('/v1/auth/token', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },

  register(name: string, email: string, password: string) {
    return apiClient.post('/v1/auth/register', { name, email, password })
  },

  logout() {
    return apiClient.post('/v1/auth/logout')
  },

  refresh() {
    return apiClient.post<Token>('/v1/auth/refresh')
  },

  requestPasswordReset(data: ResetPasswordRequestIn) {
    return apiClient.post('/v1/auth/reset-password/request', data)
  },

  resetPassword(data: ResetPasswordIn) {
    return apiClient.post('/v1/auth/reset-password', data)
  },

  switchTenant(data: SwitchTenantIn) {
    return apiClient.post<Token>('/v1/auth/switch-tenant', data)
  },
}
