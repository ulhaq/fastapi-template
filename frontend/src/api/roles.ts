import { apiClient } from './client'
import type { PaginatedResponse, RoleOut, RoleIn, RolePatch, RolePermissionIn } from '@/types'

interface ListParams {
  page_number?: number
  page_size?: number
  sort?: string
  filters?: string
}

export const rolesApi = {
  list(params: ListParams = {}) {
    return apiClient.get<PaginatedResponse<RoleOut>>('/roles', { params })
  },

  get(id: number) {
    return apiClient.get<RoleOut>(`/v1/roles/${id}`)
  },

  create(data: RoleIn) {
    return apiClient.post<RoleOut>('/roles', data)
  },

  patch(id: number, data: RolePatch) {
    return apiClient.patch<RoleOut>(`/v1/roles/${id}`, data)
  },

  delete(id: number) {
    return apiClient.delete(`/v1/roles/${id}`)
  },

  setPermissions(id: number, data: RolePermissionIn) {
    return apiClient.post<RoleOut>(`/v1/roles/${id}/permissions`, data)
  },
}
