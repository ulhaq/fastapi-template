<route lang="yaml">
meta:
  breadcrumb: gdpr.title
</route>

<template>
  <div class="max-w-2xl animate-fade-in">
    <PageHeader :title="$t('gdpr.title')" :description="$t('gdpr.description')" />

    <!-- Export Data -->
    <Card class="mt-6">
      <CardContent class="pt-6 flex items-start justify-between gap-4">
        <div>
          <p class="font-medium text-sm">{{ $t('gdpr.exportTitle') }}</p>
          <p class="text-sm text-muted-foreground mt-0.5">{{ $t('gdpr.exportDescription') }}</p>
        </div>
        <Button variant="outline" size="sm" :disabled="exporting" @click="handleExport">
          <Loader2 v-if="exporting" class="w-4 h-4 mr-2 animate-spin" />
          {{ $t('gdpr.exportButton') }}
        </Button>
      </CardContent>
    </Card>

    <!-- Delete Account -->
    <div class="mt-8">
      <h2 class="text-sm font-semibold text-destructive uppercase tracking-wider mb-3">
        {{ $t('settings.dangerZone') }}
      </h2>
      <Card class="border-destructive/50">
        <CardContent class="pt-6">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="font-medium text-sm">{{ $t('gdpr.deleteTitle') }}</p>
              <p class="text-sm text-muted-foreground mt-0.5">{{ $t('gdpr.deleteDescription') }}</p>
            </div>
            <Button
              variant="destructive"
              size="sm"
              :disabled="deleting"
              @click="showDeleteForm = true"
            >
              {{ $t('gdpr.deleteButton') }}
            </Button>
          </div>

          <form
            v-if="showDeleteForm"
            class="mt-4 space-y-3 border-t pt-4"
            @submit.prevent="handleDelete"
          >
            <div class="space-y-2">
              <Label for="delete-password">{{ $t('gdpr.deletePasswordLabel') }}</Label>
              <Input
                id="delete-password"
                v-model="deletePassword"
                type="password"
                :placeholder="$t('gdpr.deletePasswordPlaceholder')"
                :disabled="deleting"
                autofocus
              />
            </div>
            <p v-if="deleteError" class="text-sm text-destructive">{{ deleteError }}</p>
            <div class="flex gap-2 justify-end">
              <Button
                type="button"
                variant="outline"
                size="sm"
                :disabled="deleting"
                @click="cancelDelete"
              >
                {{ $t('common.cancel') }}
              </Button>
              <Button type="submit" variant="destructive" size="sm" :disabled="deleting">
                <Loader2 v-if="deleting" class="w-4 h-4 mr-2 animate-spin" />
                {{ $t('gdpr.deleteConfirm') }}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/toast'
import PageHeader from '@/components/common/PageHeader.vue'
import { gdprApi } from '@/api/gdpr'
import { useAuthStore } from '@/stores/auth'
import { useConfirm } from '@/composables/useConfirm'
import { useErrorHandler } from '@/composables/useErrorHandler'

const router = useRouter()
const { t } = useI18n()
const auth = useAuthStore()
const { confirm } = useConfirm()
const { resolveError } = useErrorHandler()
const { toast } = useToast()

const exporting = ref(false)
const deleting = ref(false)
const showDeleteForm = ref(false)
const deletePassword = ref('')
const deleteError = ref('')

async function handleExport() {
  exporting.value = true
  try {
    const { data } = await gdprApi.exportMyData()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'my-data.json'
    link.click()
    URL.revokeObjectURL(url)
    toast({ title: t('gdpr.exportSuccess') })
  } catch (err) {
    toast({ title: resolveError(err), variant: 'destructive' })
  } finally {
    exporting.value = false
  }
}

function cancelDelete() {
  showDeleteForm.value = false
  deletePassword.value = ''
  deleteError.value = ''
}

async function handleDelete() {
  const ok = await confirm(
    t('gdpr.deleteConfirmTitle'),
    t('gdpr.deleteConfirmDescription'),
    t('gdpr.deleteConfirm'),
    'destructive',
  )
  if (!ok) return

  deleting.value = true
  deleteError.value = ''
  try {
    await gdprApi.deleteMyAccount({ current_password: deletePassword.value })
    await auth.logout()
    router.push('/login')
  } catch (err) {
    deleteError.value = resolveError(err)
  } finally {
    deleting.value = false
  }
}
</script>
