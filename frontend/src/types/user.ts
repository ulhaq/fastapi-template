import type { Role } from '@/types/role'

export interface User {
  id: number
  name: string
  email: string
  roles?: Role[]
  role_ids?: number[]
  created_at?: string
  updated_at?: string
}
