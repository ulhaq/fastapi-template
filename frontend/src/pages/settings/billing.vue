<route lang="yaml">
meta:
  permission: manage:subscription
  breadcrumb: nav.subscription
</route>

<template>
  <div class="animate-fade-in space-y-6">
    <PageHeader :title="$t('subscription.title')" :description="$t('subscription.description')" />

    <!-- Loading skeleton -->
    <div v-if="isLoading" class="space-y-4">
      <Skeleton class="h-48 w-full rounded-lg" />
    </div>

    <!-- Pending checkout card (incomplete subscription - edge case) -->
    <template v-else-if="subscription?.status === 'incomplete'">
      <div class="rounded-lg border p-6 space-y-4">
        <div>
          <h3 class="font-semibold text-lg">{{ $t('subscription.startSubscriptionTitle') }}</h3>
          <p class="text-muted-foreground text-sm mt-0.5">{{ $t('subscription.incompleteNotice') }}</p>
        </div>

        <div v-if="subscription.plan_price" class="text-2xl font-bold">
          {{ formatPrice(subscription.plan_price) }}
          <span class="text-sm font-normal text-muted-foreground">/ {{ subscription.plan_price.interval }}</span>
        </div>

        <PermissionGuard v-if="subscription.plan_price_id" permission="manage:subscription">
          <Button @click="handleCheckout(subscription.plan_price_id!)" :disabled="isCheckingOut">
            <Loader2 v-if="isCheckingOut" class="w-4 h-4 mr-2 animate-spin" />
            {{ $t('subscription.subscribe') }}
          </Button>
        </PermissionGuard>
      </div>
    </template>

    <!-- Free plan card (active free subscription - show trial/upgrade CTA) -->
    <template v-else-if="subscription?.status === 'active' && subscription.plan_price?.amount === 0">
      <div class="rounded-lg border p-6 space-y-4">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="font-semibold text-lg">{{ $t('subscription.currentPlan') }}</h3>
            <p class="text-muted-foreground text-sm mt-0.5">
              <Skeleton v-if="plansLoading" class="h-4 w-16 inline-block" />
              <span v-else>{{ planName(subscription.plan_price) || $t('subscription.free') }}</span>
            </p>
          </div>
          <Badge :class="statusBadgeClass('active')" variant="outline">
            {{ $t('subscription.status.active') }}
          </Badge>
        </div>

        <div v-if="subscription.plan_price" class="text-2xl font-bold">
          {{ formatPrice(subscription.plan_price) }}
          <span class="text-sm font-normal text-muted-foreground">/ {{ subscription.plan_price.interval }}</span>
        </div>

        <PermissionGuard v-if="subscription.trial_end" permission="manage:subscription">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <Button variant="outline" @click="handlePortal" :disabled="isPortalLoading">
                  <Loader2 v-if="isPortalLoading" class="w-4 h-4 mr-2 animate-spin" />
                  <ExternalLink v-else class="w-4 h-4 mr-2" />
                  {{ $t('subscription.manageBilling') }}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{{ $t('subscription.manageBillingTooltip') }}</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </PermissionGuard>

      </div>

      <!-- Trial CTA card - separate from the current plan card -->
      <div v-if="!plansLoading && trialPrice && !subscription.trial_used" class="rounded-lg border border-primary/20 p-6 space-y-3">
        <div>
          <h3 class="font-semibold text-lg">{{ $t('subscription.startTrialTitle') }}</h3>
          <p class="text-muted-foreground text-sm mt-0.5">
            {{ $t('subscription.heroTrialSubtitle', { days: trialPrice.trial_period_days, price: formatPrice(trialPrice), interval: trialPrice.interval }) }}
          </p>
        </div>
        <div class="flex items-center gap-4">
          <PermissionGuard permission="manage:subscription">
            <Button @click="handleTrial(trialPrice.id)" :disabled="isTrialing">
              <Loader2 v-if="isTrialing" class="w-4 h-4 mr-2 animate-spin" />
              {{ $t('subscription.startTrialButton') }}
            </Button>
          </PermissionGuard>
          <span class="inline-flex items-center gap-1.5 rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800">
            <ShieldCheck class="w-3.5 h-3.5 shrink-0" />
            {{ $t('subscription.noCardRequired') }}
          </span>
        </div>
      </div>

      <!-- Plan picker - lets the user choose a specific plan -->
      <div v-if="plansLoading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Skeleton v-for="n in 3" :key="n" class="h-36 w-full rounded-lg" />
      </div>
      <div v-else-if="availablePlans.filter(p => p.prices.some(pr => pr.is_active)).length > 0" class="space-y-3">
        <h3 class="font-semibold">{{ $t('subscription.availablePlans') }}</h3>
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="plan in availablePlans.filter(p => p.prices.some(pr => pr.is_active))"
            :key="plan.id"
            class="rounded-lg border p-4 space-y-3"
          >
            <div class="flex items-start justify-between gap-2">
              <div>
                <h4 class="font-semibold">{{ plan.name }}</h4>
                <p v-if="plan.description" class="text-xs text-muted-foreground mt-0.5">{{ plan.description }}</p>
              </div>
              <span
                v-if="plan.prices.some(p => p.amount > 0 && p.is_active && p.trial_period_days) && !subscription?.trial_used"
                class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800 shrink-0"
              >
                <ShieldCheck class="w-3 h-3 shrink-0" />
                {{ $t('subscription.noCardRequired') }}
              </span>
            </div>
            <div class="space-y-2">
              <div
                v-for="price in plan.prices.filter(p => p.is_active)"
                :key="price.id"
                class="flex items-center justify-between gap-2"
              >
                <div>
                  <span class="text-sm font-medium">{{ price.amount === 0 ? $t('subscription.free') : formatPrice(price) }}</span>
                  <span v-if="price.amount > 0" class="text-xs text-muted-foreground"> / {{ price.interval }}</span>
                </div>
                <PermissionGuard permission="manage:subscription">
                  <Button v-if="price.amount === 0" size="sm" disabled>
                    {{ $t('subscription.currentPlan') }}
                  </Button>
                  <Button
                    v-else-if="price.trial_period_days && !subscription.trial_used"
                    size="sm"
                    @click="handleTrial(price.id)"
                    :disabled="trialId === price.id || isTrialing"
                  >
                    <Loader2 v-if="trialId === price.id" class="w-4 h-4 mr-2 animate-spin" />
                    {{ $t('subscription.startTrialButton') }}
                  </Button>
                  <Button v-else size="sm" @click="handleCheckout(price.id)" :disabled="checkoutId === price.id || isCheckingOut">
                    <Loader2 v-if="checkoutId === price.id" class="w-4 h-4 mr-2 animate-spin" />
                    {{ $t('subscription.subscribe') }}
                  </Button>
                </PermissionGuard>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Paused card (trial ended, no payment method) -->
    <template v-else-if="subscription?.status === 'paused'">
      <div class="rounded-lg border p-6 space-y-4">
        <div>
          <h3 class="font-semibold text-lg">{{ $t('subscription.trialEndedTitle') }}</h3>
          <p class="text-muted-foreground text-sm mt-0.5">
            {{ $t('subscription.trialEndedDescription', { plan: planName(subscription.plan_price) }) }}
          </p>
        </div>

        <div v-if="subscription.plan_price" class="text-2xl font-bold">
          {{ formatPrice(subscription.plan_price) }}
          <span class="text-sm font-normal text-muted-foreground">/ {{ subscription.plan_price.interval }}</span>
        </div>

        <PermissionGuard permission="manage:subscription">
          <Button @click="handlePortal" :disabled="isPortalLoading">
            <Loader2 v-if="isPortalLoading" class="w-4 h-4 mr-2 animate-spin" />
            {{ $t('subscription.addPaymentMethod') }}
          </Button>
        </PermissionGuard>
      </div>

      <!-- Available paid plans to subscribe to from the paused state -->
      <div v-if="paidPlans.length > 0" class="space-y-3">
        <h3 class="font-semibold">{{ $t('subscription.availablePlans') }}</h3>
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="plan in paidPlans"
            :key="plan.id"
            class="rounded-lg border p-4 space-y-3"
          >
            <div>
              <h4 class="font-semibold">{{ plan.name }}</h4>
              <p v-if="plan.description" class="text-xs text-muted-foreground mt-0.5">{{ plan.description }}</p>
            </div>
            <div class="space-y-2">
              <div
                v-for="price in plan.prices.filter(p => p.is_active && p.amount > 0)"
                :key="price.id"
                class="flex items-center justify-between gap-2"
              >
                <div>
                  <span class="text-sm font-medium">{{ formatPrice(price) }}</span>
                  <span class="text-xs text-muted-foreground"> / {{ price.interval }}</span>
                </div>
                <PermissionGuard permission="manage:subscription">
                  <Button size="sm" @click="handleSwitchPlan(price.id, price.amount)" :disabled="switchId === price.id || price.id === subscription?.plan_price_id">
                    <Loader2 v-if="switchId === price.id" class="w-4 h-4 mr-2 animate-spin" />
                    {{ price.id === subscription?.plan_price_id ? $t('subscription.currentPlan') : $t('subscription.subscribe') }}
                  </Button>
                </PermissionGuard>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Active subscription card -->
    <template v-else-if="subscription">
      <div class="rounded-lg border p-6 space-y-4">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="font-semibold text-lg">{{ $t('subscription.currentPlan') }}</h3>
            <p class="text-muted-foreground text-sm mt-0.5">
              {{ subscription.plan_price ? planName(subscription.plan_price) : $t('subscription.unknownPlan') }}
            </p>
          </div>
          <Badge :class="statusBadgeClass(subscription.status)" class="shrink-0 border" variant="outline">
            {{ $t(`subscription.status.${subscription.status}`) }}
          </Badge>
        </div>

        <!-- Trial-ending banner -->
        <div v-if="subscription.status === 'trialing' && subscription.trial_end">
          <!-- No payment method yet -->
          <div v-if="!subscription.has_payment_method" class="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 flex items-start justify-between gap-4">
            <p class="text-sm text-amber-800">
              {{ $t('subscription.trialEndsIn', { date: formatDateTime(subscription.trial_end) }) }}
            </p>
            <PermissionGuard permission="manage:subscription">
              <button class="text-sm font-medium text-amber-900 underline whitespace-nowrap" :disabled="isPortalLoading" @click="handlePortal">
                {{ $t('subscription.addPaymentMethod') }}
              </button>
            </PermissionGuard>
          </div>
          <!-- Payment method already on file -->
          <div v-else class="rounded-md border border-green-200 bg-green-50 px-4 py-3">
            <p class="text-sm text-green-800">
              {{ $t('subscription.trialEndsAllSet', { date: formatDateTime(subscription.trial_end) }) }}
            </p>
          </div>
        </div>

        <!-- Cancellation pending banner -->
        <div v-if="subscription.cancel_at_period_end && subscription.current_period_end" class="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 flex items-start justify-between gap-4">
          <p class="text-sm text-amber-800">
            {{ $t('subscription.cancelPending', { date: formatDate(subscription.current_period_end) }) }}
          </p>
          <PermissionGuard permission="manage:subscription">
            <button class="text-sm font-medium text-amber-900 underline whitespace-nowrap" :disabled="isActing" @click="handleResume">
              {{ $t('subscription.resumeSubscription') }}
            </button>
          </PermissionGuard>
        </div>

        <div v-if="subscription.plan_price" class="text-2xl font-bold">
          {{ formatPrice(subscription.plan_price) }}
          <span class="text-sm font-normal text-muted-foreground">/ {{ subscription.plan_price.interval }}</span>
        </div>

        <p v-if="subscription.current_period_end && !subscription.cancel_at_period_end" class="text-sm text-muted-foreground">
          {{ $t('subscription.renewsOn', { date: formatDate(subscription.current_period_end) }) }}
        </p>

        <div class="flex gap-2 flex-wrap">
          <PermissionGuard permission="manage:subscription">
            <Button v-if="subscription.cancel_at_period_end" @click="handleResume" :disabled="isActing">
              <Loader2 v-if="isActing" class="w-4 h-4 mr-2 animate-spin" />
              {{ $t('subscription.resumeSubscription') }}
            </Button>
            <Button v-else variant="outline" @click="handleCancel" :disabled="isActing">
              <Loader2 v-if="isActing" class="w-4 h-4 mr-2 animate-spin" />
              {{ $t('subscription.cancelSubscription') }}
            </Button>
          </PermissionGuard>
          <PermissionGuard permission="manage:subscription">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger as-child>
                  <Button variant="outline" @click="handlePortal" :disabled="isPortalLoading">
                    <Loader2 v-if="isPortalLoading" class="w-4 h-4 mr-2 animate-spin" />
                    <ExternalLink v-else class="w-4 h-4 mr-2" />
                    {{ $t('subscription.manageBilling') }}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{{ $t('subscription.manageBillingTooltip') }}</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </PermissionGuard>
        </div>
      </div>

      <!-- Available paid plans for upgrading/downgrading.
           Free plan is excluded - to return to free, cancel the subscription. -->
      <div v-if="paidPlans.length > 0" class="space-y-3">
        <h3 class="font-semibold">{{ $t('subscription.availablePlans') }}</h3>
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="plan in paidPlans"
            :key="plan.id"
            class="rounded-lg border p-4 space-y-3"
          >
            <div>
              <h4 class="font-semibold">{{ plan.name }}</h4>
              <p v-if="plan.description" class="text-xs text-muted-foreground mt-0.5">{{ plan.description }}</p>
            </div>
            <div class="space-y-2">
              <div
                v-for="price in plan.prices.filter(p => p.is_active && p.amount > 0)"
                :key="price.id"
                class="flex items-center justify-between gap-2"
              >
                <div>
                  <span class="text-sm font-medium">{{ formatPrice(price) }}</span>
                  <span class="text-xs text-muted-foreground"> / {{ price.interval }}</span>
                </div>
                <PermissionGuard permission="manage:subscription">
                  <Button size="sm" @click="handleSwitchPlan(price.id, price.amount)" :disabled="switchId === price.id || price.id === subscription?.plan_price_id">
                    <Loader2 v-if="switchId === price.id" class="w-4 h-4 mr-2 animate-spin" />
                    {{ price.id === subscription?.plan_price_id ? $t('subscription.currentPlan') : (subscription?.plan_price && monthlyEquivalent(price) > monthlyEquivalent(subscription.plan_price)) ? $t('subscription.upgrade') : $t('subscription.downgrade') }}
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
          <h3 class="font-semibold text-lg">{{ $t('subscription.noSubscription') }}</h3>
          <p class="text-muted-foreground text-sm mt-0.5">{{ $t('subscription.choosePlan') }}</p>
        </div>

        <div v-if="plansLoading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Skeleton v-for="n in 3" :key="n" class="h-36 w-full rounded-lg" />
        </div>
        <p v-else-if="availablePlans.length === 0" class="text-sm text-muted-foreground">
          {{ $t('subscription.noPlansAvailable') }}
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
              {{ $t('subscription.noPricesAvailable') }}
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
                    {{ $t('subscription.subscribe') }}
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loader2, ExternalLink, ShieldCheck } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import PageHeader from '@/components/common/PageHeader.vue'
import PermissionGuard from '@/components/common/PermissionGuard.vue'
import { billingApi } from '@/api/billing'
import { useSubscriptionStore } from '@/stores/subscription'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { useErrorHandler } from '@/composables/useErrorHandler'
import type { SubscriptionOut, PlanOut, PlanPriceOut } from '@/types'

const subscriptionStore = useSubscriptionStore()
const { t, locale } = useI18n()
const { toast } = useToast()
const { confirm } = useConfirm()
const { resolveError } = useErrorHandler()

const isLoading = ref(false)
const plansLoading = ref(false)
const isActing = ref(false)
const isPortalLoading = ref(false)
const checkoutId = ref<number | undefined>(undefined)
const isCheckingOut = ref(false)
const isTrialing = ref(false)
const trialId = ref<number | undefined>(undefined)
const switchId = ref<number | undefined>(undefined)
const subscription = ref<SubscriptionOut | null>(null)
const availablePlans = ref<PlanOut[]>([])

const trialPrice = computed<PlanPriceOut | undefined>(() => {
  for (const price of availablePlans.value[availablePlans.value.length - 1].prices) {
    if (price.is_active && price.amount > 0 && price.trial_period_days) {
      return price
    }
  }
  return undefined
})

const paidPlans = computed(() =>
  availablePlans.value.filter(p => p.prices.some(pr => pr.is_active && pr.amount > 0))
)
const errorMessage = ref('')

async function loadSubscription() {
  isLoading.value = true
  try {
    const { data } = await billingApi.getCurrentSubscription()
    subscription.value = data
    subscriptionStore.subscriptionStatus = data.status
    subscriptionStore.subscriptionTrialEnd = data.trial_end
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
    availablePlans.value = data
      .filter((p) => p.is_active)
      .sort((a, b) => {
        const minPrice = (plan: typeof a) =>
          Math.min(...plan.prices.filter((p) => p.is_active).map((p) => p.amount), Infinity)
        return minPrice(a) - minPrice(b)
      })
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

function planName(price: PlanPriceOut | null): string {
  if (!price) return ''
  const plan = availablePlans.value.find((p) => p.prices.some((pr) => pr.id === price.id))
  return plan?.name ?? ''
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(locale.value, { year: 'numeric', month: 'long', day: 'numeric' })
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(locale.value, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function monthlyEquivalent(price: PlanPriceOut): number {
  const count = price.interval_count ?? 1
  return price.interval === 'year' ? price.amount / (12 * count) : price.amount / count
}

function statusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    active: 'bg-green-100 text-green-800 border-green-200',
    trialing: 'bg-blue-100 text-blue-800 border-blue-200',
    past_due: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    canceled: 'bg-gray-100 text-gray-600 border-gray-200',
    incomplete: 'bg-red-100 text-red-600 border-red-200',
    paused: 'bg-orange-100 text-orange-800 border-orange-200',
  }
  return map[status] ?? ''
}

async function handleCancel() {
  const ok = await confirm(
    t('subscription.cancelTitle'),
    t('subscription.cancelDescription'),
    t('subscription.cancelConfirm'),
  )
  if (!ok) return
  isActing.value = true
  try {
    const { data } = await billingApi.cancelSubscription()
    subscription.value = data
    toast({ title: t('subscription.cancelScheduledSuccess') })
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
    toast({ title: t('subscription.resumed') })
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
    window.open(data.portal_url, '_blank', 'noopener,noreferrer')
  } catch (err: unknown) {
    toast({ title: resolveError(err), variant: 'destructive' })
  } finally {
    isPortalLoading.value = false
  }
}

async function handleSwitchPlan(priceId: number, priceAmount: number) {
  const currentAmount = subscription.value?.plan_price?.amount ?? 0
  const isUpgrade = priceAmount > currentAmount
  const isFreeToPaid = currentAmount === 0
  const ok = await confirm(
    t('subscription.switchPlanTitle'),
    t(isFreeToPaid ? 'subscription.switchPlanCheckoutDescription' : 'subscription.switchPlanDescription'),
    t(isUpgrade ? 'subscription.upgrade' : 'subscription.downgrade'),
    isUpgrade ? 'default' : 'destructive',
  )
  if (!ok) return
  switchId.value = priceId
  try {
    const { data } = await billingApi.switchPlan({ plan_price_id: priceId })
    if ('checkout_url' in data) {
      switchId.value = undefined
      window.location.href = data.checkout_url
    } else {
      subscription.value = data
      subscriptionStore.subscriptionStatus = data.status
      subscriptionStore.subscriptionTrialEnd = data.trial_end
      toast({ title: t('subscription.switchPlanSuccess') })
      switchId.value = undefined
    }
  } catch (err: unknown) {
    toast({ title: resolveError(err), variant: 'destructive' })
    switchId.value = undefined
  }
}

async function handleTrial(priceId: number) {
  trialId.value = priceId
  isTrialing.value = true
  try {
    const { data } = await billingApi.startTrial({ plan_price_id: priceId })
    window.location.href = data.checkout_url
  } catch (err: unknown) {
    toast({ title: resolveError(err), variant: 'destructive' })
    trialId.value = undefined
    isTrialing.value = false
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
