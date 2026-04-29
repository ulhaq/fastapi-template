<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ isEdit ? $t('organizations.form.editTitle') : $t('organizations.form.createTitle') }}</DialogTitle>
        <DialogDescription>
          {{ isEdit ? $t('organizations.form.editDescription') : $t('organizations.form.createDescription') }}
        </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label>{{ $t('common.name') }}</Label>
          <Input v-model="form.name" :placeholder="$t('organizations.form.namePlaceholder')" :disabled="isLoading" />
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
import { ref, computed, watch } from 'vue'
import { Loader2 } from 'lucide-vue-next'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { organizationsApi } from '@/api/organizations'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useOrganizationStore } from '@/stores/organization'
import { useValidation } from '@/composables/useValidation'
import { useRules } from '@/composables/useRules'
import type { OrganizationOut } from '@/types'

const props = defineProps<{ open: boolean; organization?: OrganizationOut | null }>()
const emit = defineEmits<{ 'update:open': [boolean]; saved: [] }>()

const { resolveError, resolveFieldErrors } = useErrorHandler()
const organizationStore = useOrganizationStore()
const rules = useRules()
const isEdit = computed(() => !!props.organization)
const { form, errors, validate, clearErrors } = useValidation({ name: rules.required })
const isLoading = ref(false)
const errorMessage = ref('')

watch(() => props.organization, (organization) => {
  form.name = organization?.name ?? ''
  clearErrors()
  errorMessage.value = ''
}, { immediate: true })

async function onSubmit() {
  if (!validate()) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (isEdit.value && props.organization) {
      await organizationsApi.patch(props.organization.id, { name: form.name })
    } else {
      await organizationsApi.create({ name: form.name })
    }
    await organizationStore.fetchOrganizations()
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
