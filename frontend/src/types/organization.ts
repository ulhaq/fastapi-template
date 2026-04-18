export interface OrganizationBase {
  name: string
}

export interface OrganizationPatch {
  name?: string
}

export interface OrganizationOut extends OrganizationBase {
  id: number
  created_at: string
  updated_at: string
}
