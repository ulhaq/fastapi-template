<template>
  <div
    v-if="showBanner"
    class="border-b border-amber-200 bg-amber-50 px-4 py-2.5 flex items-center justify-between gap-4"
  >
    <p class="text-sm text-amber-800">
      {{ $t('billing.trialEnding', { time: timeRemaining }) }}
    </p>
    <RouterLink
      to="/settings/billing"
      class="shrink-0 text-sm font-medium text-amber-800 underline underline-offset-2 hover:text-amber-900"
    >
      {{ $t('billing.manageBilling') }}
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatDuration, intervalToDuration } from 'date-fns'
import { da as daLocale } from 'date-fns/locale'
import { useAuthStore } from '@/stores/auth'

const { locale } = useI18n()
const authStore = useAuthStore()

const showBanner = computed(
  () => authStore.subscriptionStatus === 'trialing' && authStore.subscriptionTrialEnd !== null,
)

const timeRemaining = computed(() => {
  if (!authStore.subscriptionTrialEnd) return ''
  const end = new Date(authStore.subscriptionTrialEnd)
  const now = new Date()

  if (end <= now) return ''

  const duration = intervalToDuration({ start: now, end })
  const moreThan24h = end.getTime() - now.getTime() >= 24 * 60 * 60 * 1000
  return formatDuration(duration, {
    format: moreThan24h ? ['days', 'hours'] : ['hours', 'minutes'],
    locale: locale.value === 'da' ? daLocale : undefined,
  })
})
</script>
