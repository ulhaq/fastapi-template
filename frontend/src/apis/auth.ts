import type { Token } from '@/types/auth'
import type { User } from '@/types/user'
import axios from '@/apis/base'

export default {
  async getToken(email: string, password: string): Promise<Token> {
    const response = await axios.post(
      '/auth/token',
      { username: email, password },
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      },
    )
    return response.data
  },

  async refreshToken(): Promise<Token> {
    const response = await axios.post('/auth/refresh')
    return response.data
  },

  async logout(): Promise<void> {
    await axios.post('/auth/logout')
  },

  async getAuthenticatedUser(): Promise<User> {
    const response = await axios.get('/users/me')
    return response.data
  },

  async register(name: string, email: string, password: string): Promise<User> {
    const response = await axios.post('/auth/register', {
      name,
      email,
      password,
    })
    return response.data
  },

  async requestPasswordReset(email: string): Promise<any> {
    const response = await axios.post('/auth/reset-password', { email })
    return response.data
  },

  async resetPassword(password: string, token: string): Promise<any> {
    const response = await axios.post(`/auth/reset-password/${token}`, {
      password,
    })
    return response.data
  },
}
