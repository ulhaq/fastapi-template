<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ isEdit ? $t('roles.form.editTitle') : $t('roles.form.createTitle') }}</DialogTitle>
        <DialogDescription>
          {{ isEdit ? $t('roles.form.editDescription') : $t('roles.form.createDescription') }}
        </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label>{{ $t('common.name') }}</Label>
          <Input v-model="form.name" :placeholder="$t('roles.form.namePlaceholder')" :disabled="isLoading" />
          <p v-if="errors.name" class="text-xs text-destructive">{{ errors.name }}</p>
        </div>
        <div class="space-y-2">
          <Label>{{ $t('common.description') }} <span class="text-muted-foreground">({{ $t('common.optional') }})</span></Label>
          <Textarea v-model="form.description" :placeholder="$t('roles.form.descriptionPlaceholder')" :disabled="isLoading" rows="3" />
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
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { rolesApi } from '@/api/roles'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useValidation } from '@/composables/useValidation'
import { useRules } from '@/composables/useRules'
import type { RoleOut } from '@/types'

const props = defineProps<{ open: boolean; role?: RoleOut | null }>()
const emit = defineEmits<{ 'update:open': [boolean]; saved: [] }>()

const { resolveError, resolveFieldErrors } = useErrorHandler()
const rules = useRules()
const isEdit = computed(() => !!props.role)
const { form, errors, validate, clearErrors } = useValidation({
  name: rules.required,
  description: [],
})
const isLoading = ref(false)
const errorMessage = ref('')

watch(() => props.role, (r) => {
  form.name = r?.name ?? ''
  form.description = r?.description ?? ''
  clearErrors()
  errorMessage.value = ''
}, { immediate: true })

async function onSubmit() {
  if (!validate()) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    const payload = { name: form.name, description: form.description || null }
    if (isEdit.value && props.role) {
      await rolesApi.patch(props.role.id, payload)
    } else {
      await rolesApi.create(payload)
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
