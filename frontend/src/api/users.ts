import { apiClient } from './client'
import type { PaginatedResponse, UserOut, UserPatch, UserRoleIn, OrganizationOut, ChangePasswordIn } from '@/types'

interface ListParams {
  page_number?: number
  page_size?: number
  sort?: string
  filters?: string
}

export const usersApi = {
  list(params: ListParams = {}) {
    return apiClient.get<PaginatedResponse<UserOut>>('/users', { params })
  },

  getMe() {
    return apiClient.get<UserOut>('/users/me')
  },

  getMyOrganizations() {
    return apiClient.get<OrganizationOut[]>('/organizations')
  },

  get(id: number) {
    return apiClient.get<UserOut>(`/v1/users/${id}`)
  },

  patch(id: number, data: UserPatch) {
    return apiClient.patch<UserOut>(`/v1/users/${id}`, data)
  },

  patchMe(data: UserPatch) {
    return apiClient.patch<UserOut>('/users/me', data)
  },

  changePassword(data: ChangePasswordIn) {
    return apiClient.put<UserOut>('/users/me/change-password', data)
  },

  removeFromOrganization(id: number) {
    return apiClient.delete(`/v1/users/${id}`)
  },

  setRoles(id: number, data: UserRoleIn) {
    return apiClient.post<UserOut>(`/v1/users/${id}/roles`, data)
  },

  invite(data: { email: string; role_ids: number[] }) {
    return apiClient.post('/users/invite', data)
  },
}
