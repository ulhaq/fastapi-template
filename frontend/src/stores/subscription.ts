import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { billingApi } from '@/api/billing'

export const useSubscriptionStore = defineStore('subscription', () => {
  const subscriptionStatus = ref<string | null>(null)
  const subscriptionTrialEnd = ref<string | null>(null)
  const planFeatures = ref<string[]>([])

  const hasActiveSubscription = computed(
    () => subscriptionStatus.value === 'active' || subscriptionStatus.value === 'trialing',
  )

  function hasFeature(feature: string): boolean {
    return planFeatures.value.includes(feature)
  }

  async function fetchSubscriptionStatus(): Promise<void> {
    try {
      const { data } = await billingApi.getCurrentSubscription()
      subscriptionStatus.value = data.status
      subscriptionTrialEnd.value = data.trial_end
      planFeatures.value = data.features
    } catch {
      subscriptionStatus.value = null
      subscriptionTrialEnd.value = null
      planFeatures.value = []
    }
  }

  function clear(): void {
    subscriptionStatus.value = null
    subscriptionTrialEnd.value = null
    planFeatures.value = []
  }

  return {
    subscriptionStatus,
    subscriptionTrialEnd,
    planFeatures,
    hasActiveSubscription,
    hasFeature,
    fetchSubscriptionStatus,
    clear,
  }
})
