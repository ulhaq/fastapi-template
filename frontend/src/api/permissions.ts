import { apiClient } from './client'
import type { PaginatedResponse, PermissionOut } from '@/types'

interface ListParams {
  page_number?: number
  page_size?: number
  sort?: string
  filters?: string
}

export const permissionsApi = {
  list(params: ListParams = {}) {
    return apiClient.get<PaginatedResponse<PermissionOut>>('/v1/permissions', { params })
  },

  get(id: number) {
    return apiClient.get<PermissionOut>(`/v1/permissions/${id}`)
  },
}
