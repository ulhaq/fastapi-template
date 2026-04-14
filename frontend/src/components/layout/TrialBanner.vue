<template>
  <div
    v-if="showBanner"
    class="border-b border-amber-200 bg-amber-50 px-4 py-2.5 flex items-center justify-between gap-4"
  >
    <p class="text-sm text-amber-800">
      {{ bannerText }}
    </p>
    <RouterLink
      to="/settings/billing"
      class="shrink-0 text-sm font-medium text-amber-800 underline underline-offset-2 hover:text-amber-900"
    >
      {{ t('billing.manageBilling') }}
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()

const showBanner = computed(
  () =>
    authStore.subscriptionStatus === 'trialing' &&
    authStore.trialDaysRemaining !== null &&
    authStore.trialDaysRemaining <= 7,
)

const bannerText = computed(() => {
  const days = authStore.trialDaysRemaining
  if (days === 0) return t('billing.banner.trialEndingToday')
  if (days === 1) return t('billing.banner.trialEndingTomorrow')
  return t('billing.banner.trialEnding', { days })
})
</script>
