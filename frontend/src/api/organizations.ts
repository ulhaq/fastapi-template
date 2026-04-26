import { apiClient } from './client'
import type { PaginatedResponse, OrganizationOut, OrganizationBase, OrganizationPatch, UserOut } from '@/types'

export const organizationsApi = {
  list() {
    return apiClient.get<OrganizationOut[]>('/v1/organizations')
  },

  get(id: number) {
    return apiClient.get<OrganizationOut>(`/v1/organizations/${id}`)
  },

  create(data: OrganizationBase) {
    return apiClient.post<OrganizationOut>('/v1/organizations', data)
  },

  patch(id: number, data: OrganizationPatch) {
    return apiClient.patch<OrganizationOut>(`/v1/organizations/${id}`, data)
  },

  delete(id: number) {
    return apiClient.delete(`/v1/organizations/${id}`)
  },

  getUsers(organizationId: number) {
    return apiClient.get<PaginatedResponse<UserOut>>(`/v1/organizations/${organizationId}/users`)
  },

  transferOwnership(organizationId: number, userId: number) {
    return apiClient.post(`/v1/organizations/${organizationId}/transfer-ownership`, { user_id: userId })
  },
}
