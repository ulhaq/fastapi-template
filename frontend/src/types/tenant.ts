export interface TenantBase {
  name: string
}

export interface TenantPatch {
  name?: string
}

export interface TenantOut extends TenantBase {
  id: number
  created_at: string
  updated_at: string
}
