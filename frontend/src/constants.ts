export const OWNER_ROLE_NAME = 'Owner'

export const PlanFeature = {
  API_ACCESS: 'api_access',
} as const

export type PlanFeatureValue = (typeof PlanFeature)[keyof typeof PlanFeature]
export const PASSWORD_MIN_LENGTH = 8

export const PAGE_SIZE = 100
export const PAGE_SIZE_DASHBOARD = 10

export const BADGE_MAX = 4

export const MS_PER_DAY = 24 * 60 * 60 * 1000
