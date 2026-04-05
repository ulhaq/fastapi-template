<route lang="yaml">
meta:
  layout: dashboard
  requiresAuth: true
  breadcrumb: billing.checkoutSuccess
</route>

<template>
  <div class="animate-fade-in space-y-6">
    <PageHeader :title="$t('billing.title')" />

    <div v-if="isLoading" class="space-y-4">
      <Skeleton class="h-48 w-full rounded-lg" />
    </div>

    <div v-else-if="isSuccess" class="rounded-lg border p-6 space-y-4">
      <div>
        <h3 class="font-semibold text-lg">{{ $t('billing.checkoutSuccess') }}</h3>
        <p class="text-muted-foreground text-sm mt-0.5">{{ $t('billing.checkoutSuccessDescription') }}</p>
      </div>
      <Button @click="router.push('/')">{{ $t('billing.goToDashboard') }}</Button>
    </div>

    <div v-else-if="isPending" class="rounded-lg border p-6 space-y-4">
      <div>
        <h3 class="font-semibold text-lg">{{ $t('billing.checkoutPending') }}</h3>
        <p class="text-muted-foreground text-sm mt-0.5">{{ $t('billing.checkoutPendingDescription') }}</p>
      </div>
      <Button variant="outline" @click="router.push('/settings/billing')">
        {{ $t('billing.returnToBilling') }}
      </Button>
    </div>

    <div v-else class="rounded-lg border p-6 space-y-4">
      <div>
        <h3 class="font-semibold text-lg">{{ $t('errors.common') }}</h3>
        <p class="text-muted-foreground text-sm mt-0.5">{{ $t('billing.checkoutPendingDescription') }}</p>
      </div>
      <Button variant="outline" @click="router.push('/settings/billing')">
        {{ $t('billing.returnToBilling') }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import PageHeader from '@/components/common/PageHeader.vue'
import { billingApi } from '@/api/billing'

const router = useRouter()

const isLoading = ref(true)
const isSuccess = ref(false)
const isPending = ref(false)

onMounted(async () => {
  try {
    const { data } = await billingApi.getCurrentSubscription()
    if (data.status === 'active' || data.status === 'trialing') {
      isSuccess.value = true
    } else {
      isPending.value = true
    }
  } catch {
    // 404 or other error - subscription not found or error fetching
  } finally {
    isLoading.value = false
  }
})
</script>
