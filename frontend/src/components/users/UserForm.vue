<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ isEdit ? $t('users.form.editTitle') : $t('users.form.createTitle') }}</DialogTitle>
        <DialogDescription>
          {{ isEdit ? $t('users.form.editDescription') : $t('users.form.createDescription') }}
        </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label>{{ $t('common.name') }}</Label>
          <Input v-model="form.name" :placeholder="$t('users.form.namePlaceholder')" :disabled="isLoading" />
          <p v-if="errors.name" class="text-xs text-destructive">{{ errors.name }}</p>
        </div>
        <div class="space-y-2">
          <Label>{{ $t('common.email') }}</Label>
          <Input v-model="form.email" type="email" :placeholder="$t('users.form.emailPlaceholder')" :disabled="isLoading" />
          <p v-if="errors.email" class="text-xs text-destructive">{{ errors.email }}</p>
        </div>
        <div v-if="!isEdit" class="space-y-2">
          <Label>{{ $t('common.password') }}</Label>
          <Input v-model="form.password" type="password" :placeholder="$t('common.minCharacters')" :disabled="isLoading" />
          <p v-if="errors.password" class="text-xs text-destructive">{{ errors.password }}</p>
        </div>

        <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>

        <DialogFooter>
          <Button type="button" variant="outline" @click="$emit('update:open', false)" :disabled="isLoading">
            {{ $t('common.cancel') }}
          </Button>
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
import { ref, reactive, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { usersApi } from '@/api/users'
import { useErrorHandler } from '@/composables/useErrorHandler'
import type { UserOut } from '@/types'

const props = defineProps<{
  open: boolean
  user?: UserOut | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

const { t } = useI18n()
const { resolveError, resolveFieldErrors } = useErrorHandler()
const isEdit = computed(() => !!props.user)

const form = reactive({ name: '', email: '', password: '' })
const errors = reactive({ name: '', email: '', password: '' })
const isLoading = ref(false)
const errorMessage = ref('')

watch(
  () => props.user,
  (u) => {
    form.name = u?.name ?? ''
    form.email = u?.email ?? ''
    form.password = ''
    errors.name = ''
    errors.email = ''
    errors.password = ''
    errorMessage.value = ''
  },
  { immediate: true },
)

function validate() {
  errors.name = form.name.trim() ? '' : t('common.nameRequired')
  errors.email = form.email.trim() ? '' : t('common.emailRequired')
  errors.password = isEdit.value || form.password.length >= 8 ? '' : t('common.passwordMinLength')
  return !errors.name && !errors.email && !errors.password
}

async function onSubmit() {
  if (!validate()) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (isEdit.value && props.user) {
      await usersApi.patch(props.user.id, { name: form.name, email: form.email })
    } else {
      await usersApi.create({ name: form.name, email: form.email, password: form.password })
    }
    emit('update:open', false)
    emit('saved')
  } catch (err: unknown) {
    const fieldErrors = resolveFieldErrors(err)
    if (fieldErrors['body__email']) {
      errors.email = fieldErrors['body__email']
    } else if (fieldErrors['body__name']) {
      errors.name = fieldErrors['body__name']
    } else if (fieldErrors['body__password']) {
      errors.password = fieldErrors['body__password']
    } else {
      errorMessage.value = resolveError(err)
    }
  } finally {
    isLoading.value = false
  }
}
</script>
