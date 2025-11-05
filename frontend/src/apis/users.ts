import type { User } from '@/types/user'
import axios from '@/apis/base'

const endpoint = 'users'

export default {
  async create(data: User): Promise<User> {
    const response = await axios.post(endpoint, data)
    return response.data
  },

  async deleteById(id: number): Promise<void> {
    await axios.delete(`${endpoint}/${id}`)
  },

  async updateProfile(name: string, email: string): Promise<User> {
    const response = await axios.put(`${endpoint}/me`, { name, email })
    return response.data
  },

  async changePassword(
    password: string,
    newPassword: string,
    confirmPassword: string,
  ): Promise<User> {
    const response = await axios.put(`${endpoint}/me/change-password`, {
      password,
      new_password: newPassword,
      confirm_password: confirmPassword,
    })
    return response.data
  },
}
