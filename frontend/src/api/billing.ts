import { apiClient } from './client'
import type {
  PlanOut,
  SubscriptionOut,
  CheckoutOut,
  CustomerPortalOut,
  SwitchPlanOut,
} from '@/types'

export const billingApi = {
  // Plans
  listPlans() {
    return apiClient.get<PlanOut[]>('/v1/billing/plans')
  },

  getPlan(id: number) {
    return apiClient.get<PlanOut>(`/v1/billing/plans/${id}`)
  },

  // Subscriptions
  checkout(data: { plan_price_id: number }) {
    return apiClient.post<CheckoutOut>('/v1/billing/subscriptions/checkout', data)
  },

  getCurrentSubscription() {
    return apiClient.get<SubscriptionOut>('/v1/billing/subscriptions/current')
  },

  cancelSubscription() {
    return apiClient.post<SubscriptionOut>('/v1/billing/subscriptions/current/cancel')
  },

  resumeSubscription() {
    return apiClient.post<SubscriptionOut>('/v1/billing/subscriptions/current/resume')
  },

  switchPlan(data: { plan_price_id: number }) {
    return apiClient.post<SwitchPlanOut>('/v1/billing/subscriptions/current/switch-plan', data)
  },

  getPortalUrl() {
    return apiClient.get<CustomerPortalOut>('/v1/billing/subscriptions/portal')
  },
}
