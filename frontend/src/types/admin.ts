export interface OrgMemberOut {
  user_id: number
  name: string
  email: string
  roles: Array<{ id: number; name: string; description: string }>
}

export interface AdminUserOut {
  id: number
  name: string
  email: string
  created_at: string
  updated_at: string | null
  organizations: Array<{ id: number; name: string }>
}

export interface AdminOrganizationOut {
  id: number
  name: string
  created_at: string
  updated_at: string | null
  plan_name: string | null
  subscription_status: string | null
}

export interface AuditLogOut {
  id: number
  organization_id: number | null
  user_id: number | null
  action: string
  resource_type: string | null
  resource_id: number | null
  ip_address: string | null
  details: Record<string, unknown> | null
  created_at: string
}
