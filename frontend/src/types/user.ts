import type { RoleOut } from './role'

export interface UserBase {
  name: string
  email: string
}

export interface UserIn extends UserBase {
  password: string
}

export interface UserPatch {
  name?: string
  email?: string
}

export interface UserRoleIn {
  role_ids: number[]
}

export interface UserOut extends UserBase {
  id: number
  roles: RoleOut[]
  created_at: string
  updated_at: string
}
