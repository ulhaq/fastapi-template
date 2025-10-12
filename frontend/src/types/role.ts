import type { Permission } from '@/types/permission'

export interface Role {
  id: number
  name: string
  description: string
  permissions?: Permission[]
  permission_ids?: number[]
  created_at?: string
  updated_at?: string
}
