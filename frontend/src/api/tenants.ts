import { apiClient } from './client'
import type { PaginatedResponse, TenantOut, TenantBase, TenantPatch, UserOut } from '@/types'

export const tenantsApi = {
  list() {
    return apiClient.get<TenantOut[]>('/v1/tenants')
  },

  get(id: number) {
    return apiClient.get<TenantOut>(`/v1/tenants/${id}`)
  },

  create(data: TenantBase) {
    return apiClient.post<TenantOut>('/v1/tenants', data)
  },

  patch(id: number, data: TenantPatch) {
    return apiClient.patch<TenantOut>(`/v1/tenants/${id}`, data)
  },

  delete(id: number) {
    return apiClient.delete(`/v1/tenants/${id}`)
  },

  getUsers(tenantId: number) {
    return apiClient.get<PaginatedResponse<UserOut>>(`/v1/tenants/${tenantId}/users`)
  },

  addUser(tenantId: number, userId: number) {
    return apiClient.post(`/v1/tenants/${tenantId}/users/${userId}`)
  },

  removeUser(tenantId: number, userId: number) {
    return apiClient.delete(`/v1/tenants/${tenantId}/users/${userId}`)
  },
}
