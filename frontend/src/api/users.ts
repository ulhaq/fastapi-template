import { apiClient } from './client'
import type { PaginatedResponse, UserOut, UserPatch, UserRoleIn, TenantOut, ChangePasswordIn } from '@/types'

interface ListParams {
  page_number?: number
  page_size?: number
  sort?: string
  filters?: string
}

export const usersApi = {
  list(params: ListParams = {}) {
    return apiClient.get<PaginatedResponse<UserOut>>('/v1/users', { params })
  },

  getMe() {
    return apiClient.get<UserOut>('/v1/users/me')
  },

  getMyTenants() {
    return apiClient.get<TenantOut[]>('/v1/tenants')
  },

  get(id: number) {
    return apiClient.get<UserOut>(`/v1/users/${id}`)
  },

  patch(id: number, data: UserPatch) {
    return apiClient.patch<UserOut>(`/v1/users/${id}`, data)
  },

  patchMe(data: UserPatch) {
    return apiClient.patch<UserOut>('/v1/users/me', data)
  },

  changePassword(data: ChangePasswordIn) {
    return apiClient.put<UserOut>('/v1/users/me/change-password', data)
  },

  delete(id: number) {
    return apiClient.delete(`/v1/users/${id}`)
  },

  setRoles(id: number, data: UserRoleIn) {
    return apiClient.post<UserOut>(`/v1/users/${id}/roles`, data)
  },

  invite(data: { email: string; role_ids: number[] }) {
    return apiClient.post('/v1/users/invite', data)
  },
}
