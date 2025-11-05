import type { PaginatedResponse } from '@/types/common'
import type { Permission } from '@/types/permission'
import axios from '@/apis/base'

const endpoint = 'permissions'

export default {
  async getAll(
    params?: Record<string, any>,
  ): Promise<PaginatedResponse<Permission>> {
    const response = await axios.get(endpoint, { params })
    return response.data
  },

  async getById(id: number): Promise<Permission> {
    const response = await axios.get(`${endpoint}/${id}`)
    return response.data
  },

  async create(data: Permission): Promise<Permission> {
    const response = await axios.post(endpoint, data)
    return response.data
  },

  async updateById(id: number, data: Permission): Promise<Permission> {
    const response = await axios.put(`${endpoint}/${id}`, data)
    return response.data
  },

  async deleteById(id: number): Promise<void> {
    await axios.delete(`${endpoint}/${id}`)
  },
}
