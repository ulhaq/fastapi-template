<route lang="yaml">
meta:
  permission: read:subscription
  breadcrumb: nav.billing
</route>

<template>
  <div class="animate-fade-in space-y-6">
    <PageHeader :title="$t('billing.title')" :description="$t('billing.description')" />

    <!-- Loading skeleton -->
    <div v-if="isLoading" class="space-y-4">
      <Skeleton class="h-48 w-full rounded-lg" />
    </div>

    <!-- Active subscription card -->
    <template v-else-if="subscription">
      <div class="rounded-lg border p-6 space-y-4">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="font-semibold text-lg">{{ $t('billing.currentPlan') }}</h3>
            <p class="text-muted-foreground text-sm mt-0.5">
              {{ subscription.plan_price ? resolvedPlanName(subscription.plan_price) : $t('billing.unknownPlan') }}
            </p>
          </div>
          <Badge :class="statusBadgeClass(subscription.status)" class="shrink-0 border">
            {{ $t(`billing.status.${subscription.status}`) }}
          </Badge>
        </div>

        <div v-if="subscription.plan_price" class="text-2xl font-bold">
          {{ formatPrice(subscription.plan_price) }}
          <span class="text-sm font-normal text-muted-foreground">/ {{ subscription.plan_price.interval }}</span>
        </div>

        <p v-if="subscription.current_period_end" class="text-sm text-muted-foreground">
          <template v-if="subscription.cancel_at_period_end">
            {{ $t('billing.cancelScheduled', { date: formatDate(subscription.current_period_end) }) }}
          </template>
          <template v-else>
            {{ $t('billing.renewsOn', { date: formatDate(subscription.current_period_end) }) }}
          </template>
        </p>

        <div class="flex gap-2 flex-wrap">
          <PermissionGuard permission="manage:subscription">
            <Button v-if="subscription.cancel_at_period_end" @click="handleResume" :disabled="isActing">
              <Loader2 v-if="isActing" class="w-4 h-4 mr-2 animate-spin" />
              {{ $t('billing.resumeSubscription') }}
            </Button>
            <Button v-else variant="outline" @click="handleCancel" :disabled="isActing">
              <Loader2 v-if="isActing" class="w-4 h-4 mr-2 animate-spin" />
              {{ $t('billing.cancelSubscription') }}
            </Button>
          </PermissionGuard>
          <PermissionGuard v-if="subscription.status !== 'incomplete'" permission="manage:subscription">
            <Button variant="outline" @click="handlePortal" :disabled="isPortalLoading">
              <Loader2 v-if="isPortalLoading" class="w-4 h-4 mr-2 animate-spin" />
              <ExternalLink v-else class="w-4 h-4 mr-2" />
              {{ $t('billing.manageBilling') }}
            </Button>
          </PermissionGuard>
        </div>
      </div>

      <!-- Available plans for upgrading -->
      <div v-if="availablePlans.length > 0" class="space-y-3">
        <h3 class="font-semibold">{{ $t('billing.availablePlans') }}</h3>
        <p v-if="subscription.status === 'incomplete'" class="text-sm text-muted-foreground">
          {{ $t('billing.incompleteNotice') }}
        </p>
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="plan in availablePlans"
            :key="plan.id"
            class="rounded-lg border p-4 space-y-3"
          >
            <div>
              <h4 class="font-semibold">{{ plan.name }}</h4>
              <p v-if="plan.description" class="text-xs text-muted-foreground mt-0.5">{{ plan.description }}</p>
            </div>
            <p v-if="plan.prices.filter(p => p.is_active).length === 0" class="text-xs text-muted-foreground">
              {{ $t('billing.noPricesAvailable') }}
            </p>
            <div v-else class="space-y-2">
              <div
                v-for="price in plan.prices.filter(p => p.is_active)"
                :key="price.id"
                class="flex items-center justify-between gap-2"
              >
                <div>
                  <span class="text-sm font-medium">{{ formatPrice(price) }}</span>
                  <span class="text-xs text-muted-foreground"> / {{ price.interval }}</span>
                </div>
                <PermissionGuard permission="manage:subscription">
                  <Button size="sm" @click="handleSwitchPlan(price.id)" :disabled="switchId === price.id || price.id === subscription?.plan_price_id || subscription?.status === 'incomplete'">
                    <Loader2 v-if="switchId === price.id" class="w-4 h-4 mr-2 animate-spin" />
                    {{ $t('billing.switchPlan') }}
                  </Button>
                </PermissionGuard>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- No subscription - show plan selection -->
    <template v-else>
      <div class="rounded-lg border p-6 space-y-4">
        <div>
          <h3 class="font-semibold text-lg">{{ $t('billing.noSubscription') }}</h3>
          <p class="text-muted-foreground text-sm mt-0.5">{{ $t('billing.choosePlan') }}</p>
        </div>

        <div v-if="plansLoading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Skeleton v-for="n in 3" :key="n" class="h-36 w-full rounded-lg" />
        </div>
        <p v-else-if="availablePlans.length === 0" class="text-sm text-muted-foreground">
          {{ $t('billing.noPlansAvailable') }}
        </p>
        <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="plan in availablePlans"
            :key="plan.id"
            class="rounded-lg border p-4 space-y-3"
          >
            <div>
              <h4 class="font-semibold">{{ plan.name }}</h4>
              <p v-if="plan.description" class="text-xs text-muted-foreground mt-0.5">{{ plan.description }}</p>
            </div>
            <p v-if="plan.prices.filter(p => p.is_active).length === 0" class="text-xs text-muted-foreground">
              {{ $t('billing.noPricesAvailable') }}
            </p>
            <div v-else class="space-y-2">
              <div
                v-for="price in plan.prices.filter(p => p.is_active)"
                :key="price.id"
                class="flex items-center justify-between gap-2"
              >
                <div>
                  <span class="text-sm font-medium">{{ formatPrice(price) }}</span>
                  <span class="text-xs text-muted-foreground"> / {{ price.interval }}</span>
                </div>
                <PermissionGuard permission="manage:subscription">
                  <Button size="sm" @click="handleCheckout(price.id)" :disabled="checkoutId === price.id || isCheckingOut">
                    <Loader2 v-if="checkoutId === price.id" class="w-4 h-4 mr-2 animate-spin" />
                    {{ $t('billing.subscribe') }}
                  </Button>
                </PermissionGuard>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loader2, ExternalLink } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import PageHeader from '@/components/common/PageHeader.vue'
import PermissionGuard from '@/components/common/PermissionGuard.vue'
import { billingApi } from '@/api/billing'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { useErrorHandler } from '@/composables/useErrorHandler'
import type { SubscriptionOut, PlanOut, PlanPriceOut } from '@/types'

const { t } = useI18n()
const { toast } = useToast()
const { confirm } = useConfirm()
const { resolveError } = useErrorHandler()

const isLoading = ref(false)
const plansLoading = ref(false)
const isActing = ref(false)
const isPortalLoading = ref(false)
const checkoutId = ref<number | undefined>(undefined)
const isCheckingOut = ref(false)
const switchId = ref<number | undefined>(undefined)
const subscription = ref<SubscriptionOut | null>(null)
const availablePlans = ref<PlanOut[]>([])
const errorMessage = ref('')

async function loadSubscription() {
  isLoading.value = true
  try {
    const { data } = await billingApi.getCurrentSubscription()
    subscription.value = data
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status
    if (status !== 404) {
      errorMessage.value = resolveError(err)
    }
  } finally {
    isLoading.value = false
  }
}

function onVisibilityChange() {
  if (document.visibilityState === 'visible') {
    loadSubscription()
  }
}

onMounted(async () => {
  await loadSubscription()

  plansLoading.value = true
  try {
    const { data } = await billingApi.listPlans()
    availablePlans.value = data.filter((p) => p.is_active)
  } catch {
    // Non-critical - plan list is optional context
  } finally {
    plansLoading.value = false
  }

  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVisibilityChange)
})

function formatPrice(price: PlanPriceOut): string {
  const amount = price.amount / 100
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: price.currency }).format(amount)
  } catch {
    return `${price.currency.toUpperCase()} ${amount.toFixed(2)}`
  }
}

function resolvedPlanName(price: PlanPriceOut): string {
  const plan = availablePlans.value.find((p) => p.prices.some((pr) => pr.id === price.id))
  return plan ? `${plan.name} - ${formatPrice(price)} / ${price.interval}` : formatPrice(price)
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

function statusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    active: 'bg-green-100 text-green-800 border-green-200',
    trialing: 'bg-blue-100 text-blue-800 border-blue-200',
    past_due: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    canceled: 'bg-gray-100 text-gray-600 border-gray-200',
    incomplete: 'bg-gray-100 text-gray-600 border-gray-200',
  }
  return map[status] ?? ''
}

async function handleCancel() {
  const isIncomplete = subscription.value?.status === 'incomplete'
  const ok = await confirm(
    t('billing.cancelTitle'),
    t(isIncomplete ? 'billing.cancelIncompleteDescription' : 'billing.cancelDescription'),
    t('billing.cancelConfirm'),
  )
  if (!ok) return
  isActing.value = true
  try {
    const { data } = await billingApi.cancelSubscription()
    subscription.value = data
    toast({ title: t('billing.cancelScheduledSuccess') })
  } catch (err: unknown) {
    toast({ title: resolveError(err), variant: 'destructive' })
  } finally {
    isActing.value = false
  }
}

async function handleResume() {
  isActing.value = true
  try {
    const { data } = await billingApi.resumeSubscription()
    subscription.value = data
    toast({ title: t('billing.resumed') })
  } catch (err: unknown) {
    toast({ title: resolveError(err), variant: 'destructive' })
  } finally {
    isActing.value = false
  }
}

async function handlePortal() {
  isPortalLoading.value = true
  try {
    const { data } = await billingApi.getPortalUrl()
    const parsed = new URL(data.portal_url)
    if (!['https:', 'http:'].includes(parsed.protocol)) throw new Error('Invalid URL protocol')
    window.open(data.portal_url, '_blank')
  } catch (err: unknown) {
    toast({ title: resolveError(err), variant: 'destructive' })
  } finally {
    isPortalLoading.value = false
  }
}

async function handleSwitchPlan(priceId: number) {
  const ok = await confirm(
    t('billing.switchPlanTitle'),
    t('billing.switchPlanDescription'),
    t('billing.switchPlanConfirm'),
  )
  if (!ok) return
  switchId.value = priceId
  try {
    const { data } = await billingApi.switchPlan({ plan_price_id: priceId })
    subscription.value = data
    toast({ title: t('billing.switchPlanSuccess') })
  } catch (err: unknown) {
    toast({ title: resolveError(err), variant: 'destructive' })
  } finally {
    switchId.value = undefined
  }
}

async function handleCheckout(priceId: number) {
  checkoutId.value = priceId
  isCheckingOut.value = true
  try {
    const { data } = await billingApi.checkout({ plan_price_id: priceId })
    window.location.href = data.checkout_url
  } catch (err: unknown) {
    toast({ title: resolveError(err), variant: 'destructive' })
    checkoutId.value = undefined
    isCheckingOut.value = false
  }
}
</script>
