<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ isEdit ? $t('tenants.form.editTitle') : $t('tenants.form.createTitle') }}</DialogTitle>
        <DialogDescription>
          {{ isEdit ? $t('tenants.form.editDescription') : $t('tenants.form.createDescription') }}
        </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label>{{ $t('common.name') }}</Label>
          <Input v-model="form.name" :placeholder="$t('tenants.form.namePlaceholder')" :disabled="isLoading" />
          <p v-if="errors.name" class="text-xs text-destructive">{{ errors.name }}</p>
        </div>

        <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>

        <DialogFooter>
          <Button type="button" variant="outline" @click="$emit('update:open', false)" :disabled="isLoading">{{ $t('common.cancel') }}</Button>
          <Button type="submit" :disabled="isLoading">
            <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
            {{ isEdit ? $t('common.saveChanges') : $t('common.create') }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { tenantsApi } from '@/api/tenants'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useAuthStore } from '@/stores/auth'
import type { TenantOut } from '@/types'

const props = defineProps<{ open: boolean; tenant?: TenantOut | null }>()
const emit = defineEmits<{ 'update:open': [boolean]; saved: [] }>()

const { t } = useI18n()
const { resolveError, resolveFieldErrors } = useErrorHandler()
const authStore = useAuthStore()
const isEdit = computed(() => !!props.tenant)
const form = reactive({ name: '' })
const errors = reactive({ name: '' })
const isLoading = ref(false)
const errorMessage = ref('')

watch(() => props.tenant, (tenant) => {
  form.name = tenant?.name ?? ''
  errors.name = ''
  errorMessage.value = ''
}, { immediate: true })

async function onSubmit() {
  errors.name = form.name.trim() ? '' : t('common.nameRequired')
  if (errors.name) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (isEdit.value && props.tenant) {
      await tenantsApi.patch(props.tenant.id, { name: form.name })
    } else {
      await tenantsApi.create({ name: form.name })
    }
    await authStore.fetchTenants()
    emit('update:open', false)
    emit('saved')
  } catch (err: unknown) {
    const fieldErrors = resolveFieldErrors(err)
    errorMessage.value = fieldErrors['body__name'] ?? resolveError(err)
  } finally {
    isLoading.value = false
  }
}
</script>
