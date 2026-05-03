<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{
          organization ? $t('admin.editOrganization') : $t('admin.createOrganization')
        }}</DialogTitle>
        <DialogDescription>{{ $t('organizations.form.editDescription') }}</DialogDescription>
      </DialogHeader>

      <form class="space-y-4" @submit.prevent="onSubmit">
        <div class="space-y-2">
          <Label>{{ $t('common.name') }}</Label>
          <Input
            v-model="form.name"
            :placeholder="$t('organizations.form.namePlaceholder')"
            :disabled="isLoading"
          />
          <p v-if="errors.name" class="text-xs text-destructive">{{ errors.name }}</p>
        </div>

        <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            :disabled="isLoading"
            @click="$emit('update:open', false)"
          >
            {{ $t('common.cancel') }}
          </Button>
          <Button type="submit" :disabled="isLoading">
            <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
            {{ organization ? $t('common.saveChanges') : $t('common.create') }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Loader2 } from 'lucide-vue-next'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { adminApi } from '@/api/admin'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useValidation } from '@/composables/useValidation'
import { useRules } from '@/composables/useRules'
import type { OrganizationOut } from '@/types'

const props = defineProps<{ open: boolean; organization?: OrganizationOut | null }>()
const emit = defineEmits<{ 'update:open': [boolean]; saved: [] }>()

const { resolveError, resolveFieldErrors } = useErrorHandler()
const rules = useRules()
const { form, errors, validate, clearErrors } = useValidation({ name: rules.required })
const isLoading = ref(false)
const errorMessage = ref('')

watch(
  () => props.organization,
  (org) => {
    form.name = org?.name ?? ''
    clearErrors()
    errorMessage.value = ''
  },
  { immediate: true },
)

async function onSubmit() {
  if (!validate()) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (props.organization) {
      await adminApi.patchOrganization(props.organization.id, { name: form.name })
    } else {
      await adminApi.createOrganization({ name: form.name })
    }
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
