import type { PaginatedResponse } from '@/types/common'
import type { Role } from '@/types/role'
import axios from '@/apis/base'

const endpoint = 'roles'

export default {
  async getAll(params?: Record<string, any>): Promise<PaginatedResponse<Role>> {
    const response = await axios.get(endpoint, { params })
    return response.data
  },

  async getById(id: number): Promise<Role> {
    const response = await axios.get(`${endpoint}/${id}`)
    return response.data
  },

  async create(data: Role): Promise<Role> {
    const response = await axios.post(endpoint, data)
    return response.data
  },

  async updateById(id: number, data: Role): Promise<Role> {
    const response = await axios.put(`${endpoint}/${id}`, data)
    return response.data
  },

  async deleteById(id: number): Promise<void> {
    await axios.delete(`${endpoint}/${id}`)
  },

  async managePermissions(
    roleId: number | string,
    permissionIds: Array<number | string>,
  ): Promise<Role> {
    const response = await axios.post(`${endpoint}/${roleId}/permissions`, {
      permission_ids: permissionIds,
    })
    return response.data
  },
}
