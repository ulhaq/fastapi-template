import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { billingApi } from '@/api/billing'

export const useSubscriptionStore = defineStore('subscription', () => {
  const subscriptionStatus = ref<string | null>(null)
  const subscriptionTrialEnd = ref<string | null>(null)
  const hasActiveSubscription = computed(() =>
    subscriptionStatus.value === 'active' || subscriptionStatus.value === 'trialing',
  )

  async function fetchSubscriptionStatus(): Promise<void> {
    try {
      const { data } = await billingApi.getCurrentSubscription()
      subscriptionStatus.value = data.status
      subscriptionTrialEnd.value = data.trial_end
    } catch {
      subscriptionStatus.value = null
      subscriptionTrialEnd.value = null
    }
  }

  function clear(): void {
    subscriptionStatus.value = null
    subscriptionTrialEnd.value = null
  }

  return { subscriptionStatus, subscriptionTrialEnd, hasActiveSubscription, fetchSubscriptionStatus, clear }
})
