<route lang="yaml">
meta:
  breadcrumb: settings.general
</route>

<template>
  <div class="max-w-2xl animate-fade-in">
    <PageHeader :title="$t('settings.general')" />

    <div v-if="isOwner" class="mt-6">
      <h2 class="text-sm font-semibold text-destructive uppercase tracking-wider mb-3">
        {{ $t('settings.dangerZone') }}
      </h2>
      <Card class="border-destructive/50">
        <CardContent class="pt-6 flex items-start justify-between gap-4">
          <div>
            <p class="font-medium text-sm">{{ $t('settings.deleteOrganization') }}</p>
            <p class="text-sm text-muted-foreground mt-0.5">
              {{ $t('settings.deleteOrganizationDescription') }}
            </p>
          </div>
          <Button
            variant="destructive"
            size="sm"
            :disabled="deleting"
            @click="handleDeleteOrg"
          >
            <Loader2 v-if="deleting" class="w-4 h-4 mr-2 animate-spin" />
            {{ $t('settings.deleteOrganization') }}
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader.vue'
import { organizationsApi } from '@/api/organizations'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { useSessionStore } from '@/stores/session'
import { useOrganizationStore } from '@/stores/organization'
import { useConfirm } from '@/composables/useConfirm'
import { useErrorHandler } from '@/composables/useErrorHandler'

const router = useRouter()
const { t } = useI18n()
const auth = useAuthStore()
const profile = useProfileStore()
const session = useSessionStore()
const orgStore = useOrganizationStore()
const { confirm } = useConfirm()
const { handleError } = useErrorHandler()

const deleting = ref(false)

const isOwner = computed(() =>
  profile.user?.roles.some((r: any) => r.is_protected && r.name === 'Owner') ?? false
)

const activeOrgName = computed(() => {
  const org = orgStore.organizations.find(o => o.id === session.activeOrganizationId)
  return org?.name ?? ''
})

async function handleDeleteOrg() {
  const ok = await confirm(
    t('organizations.deleteTitle'),
    t('organizations.deleteDescription', { name: activeOrgName.value }),
    t('common.delete'),
  )
  if (!ok) return
  deleting.value = true
  try {
    await organizationsApi.delete(session.activeOrganizationId!)
    await auth.logout()
    router.push('/login')
  } catch (err) {
    handleError(err)
  } finally {
    deleting.value = false
  }
}
</script>
