export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginIn {
  username: string
  password: string
}

export interface ResetPasswordRequestIn {
  email: string
}

export interface ResetPasswordIn {
  token: string
  password: string
}

export interface ChangePasswordIn {
  password: string
  new_password: string
  confirm_password: string
}

export interface SwitchTenantIn {
  tenant_id: number
}

export interface JwtPayload {
  sub: string
  name?: string
  email?: string
  tid?: number
  permissions?: string[]
  exp: number
  iat: number
  jti: string
}
