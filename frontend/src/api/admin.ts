import { apiClient } from './client'
import type {
  PaginatedResponse,
  AdminUserOut,
  AdminOrganizationOut,
  AuditLogOut,
  OrgMemberOut,
  OrganizationOut,
} from '@/types'

interface ListParams {
  page_number?: number
  page_size?: number
  sort?: string
  filters?: string
}

interface AuditLogParams {
  page_number?: number
  page_size?: number
  action?: string
}

export const adminApi = {
  createOrganization(data: { name: string }) {
    return apiClient.post<OrganizationOut>('/admin/organizations', data)
  },

  listOrganizations(params: ListParams = {}) {
    return apiClient.get<PaginatedResponse<AdminOrganizationOut>>('/admin/organizations', {
      params,
    })
  },

  patchOrganization(id: number, data: { name?: string }) {
    return apiClient.patch<OrganizationOut>(`/admin/organizations/${id}`, data)
  },

  deleteOrganization(id: number) {
    return apiClient.delete(`/admin/organizations/${id}`)
  },

  listOrgMembers(orgId: number) {
    return apiClient.get<OrgMemberOut[]>(`/admin/organizations/${orgId}/members`)
  },

  addOrgMember(orgId: number, data: { email: string; role_ids?: number[] }) {
    return apiClient.post<OrgMemberOut>(`/admin/organizations/${orgId}/members`, data)
  },

  removeOrgMember(orgId: number, userId: number) {
    return apiClient.delete(`/admin/organizations/${orgId}/members/${userId}`)
  },

  listUsers(params: ListParams = {}) {
    return apiClient.get<PaginatedResponse<AdminUserOut>>('/admin/users', { params })
  },

  patchUser(id: number, data: { name?: string; email?: string }) {
    return apiClient.patch<AdminUserOut>(`/admin/users/${id}`, data)
  },

  deleteUser(id: number) {
    return apiClient.delete(`/admin/users/${id}`)
  },

  forcePasswordReset(id: number) {
    return apiClient.post(`/admin/users/${id}/force-password-reset`)
  },

  listAuditLogs(params: AuditLogParams = {}) {
    return apiClient.get<PaginatedResponse<AuditLogOut>>('/admin/audit-logs', { params })
  },
}
