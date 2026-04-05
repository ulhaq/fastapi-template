export interface PlanPriceOut {
  id: number
  plan_id: number
  amount: number
  currency: string
  interval: 'month' | 'year'
  interval_count: number
  external_price_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PlanOut {
  id: number
  name: string
  description: string | null
  external_product_id: string | null
  is_active: boolean
  prices: PlanPriceOut[]
  created_at: string
  updated_at: string
}

export interface SubscriptionOut {
  id: number
  tenant_id: number
  plan_price_id: number | null
  external_subscription_id: string | null
  external_customer_id: string | null
  status: 'incomplete' | 'active' | 'trialing' | 'past_due' | 'canceled'
  current_period_start: string | null
  current_period_end: string | null
  cancel_at_period_end: boolean
  canceled_at: string | null
  plan_price: PlanPriceOut | null
  created_at: string
  updated_at: string
}

export interface CheckoutOut {
  checkout_url: string
  external_session_id: string
}

export interface CustomerPortalOut {
  portal_url: string
}

export type SwitchPlanOut = SubscriptionOut | CheckoutOut
