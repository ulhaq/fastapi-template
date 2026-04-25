<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ $t('users.invite.dialogTitle') }}</DialogTitle>
        <DialogDescription>{{ $t('users.invite.dialogDescription') }}</DialogDescription>
      </DialogHeader>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label for="invite-email">{{ $t('common.email') }}</Label>
          <Input
            id="invite-email"
            v-model="email"
            type="email"
            :placeholder="$t('users.form.emailPlaceholder')"
            :disabled="isLoading"
            autofocus
          />
          <p v-if="errors.email" class="text-xs text-destructive">{{ errors.email }}</p>
        </div>

        <div class="space-y-2">
          <Label>{{ $t('users.invite.roles') }} <span class="text-muted-foreground text-xs">({{ $t('common.optional') }})</span></Label>
          <div v-if="loadingRoles" class="py-2 space-y-2">
            <Skeleton v-for="n in 3" :key="n" class="h-9 w-full" />
          </div>
          <div v-else class="space-y-1 max-h-48 overflow-y-auto">
            <div
              v-for="role in availableRoles"
              :key="role.id"
              class="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-muted cursor-pointer"
              @click="toggleRole(role.id)"
            >
              <Checkbox
                :model-value="selectedRoleIds.includes(role.id)"
                @click.stop="toggleRole(role.id)"
              />
              <div>
                <p class="text-sm font-medium">{{ role.name }}</p>
                <p v-if="role.description" class="text-xs text-muted-foreground">
                  {{ role.description }}
                </p>
              </div>
            </div>
            <p v-if="!availableRoles.length" class="text-sm text-muted-foreground px-3 py-2">
              {{ $t('users.roleDialog.noRoles') }}
            </p>
          </div>
        </div>

        <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            @click="$emit('update:open', false)"
            :disabled="isLoading"
          >{{ $t('common.cancel') }}</Button>
          <Button type="submit" :disabled="isLoading">
            <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
            {{ $t('users.invite.send') }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
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
import { Checkbox } from '@/components/ui/checkbox'
import { Skeleton } from '@/components/ui/skeleton'
import { usersApi } from '@/api/users'
import { rolesApi } from '@/api/roles'
import { useToast } from '@/composables/useToast'
import { useErrorHandler } from '@/composables/useErrorHandler'
import type { RoleOut } from '@/types'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ 'update:open': [boolean]; invited: [] }>()

const { t } = useI18n()
const { toast } = useToast()
const { resolveError, resolveFieldErrors } = useErrorHandler()

const email = ref('')
const errors = ref({ email: '' })
const errorMessage = ref('')
const isLoading = ref(false)

const availableRoles = ref<RoleOut[]>([])
const selectedRoleIds = ref<number[]>([])
const loadingRoles = ref(false)

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    email.value = ''
    errors.value.email = ''
    errorMessage.value = ''
    selectedRoleIds.value = []
    loadingRoles.value = true
    try {
      const { data } = await rolesApi.list({ page_size: 100 })
      availableRoles.value = data.items.filter((r) => !(r.is_protected && r.name === 'Owner'))
    } finally {
      loadingRoles.value = false
    }
  },
)

function toggleRole(id: number) {
  const idx = selectedRoleIds.value.indexOf(id)
  if (idx >= 0) selectedRoleIds.value.splice(idx, 1)
  else selectedRoleIds.value.push(id)
}

function validate() {
  errors.value.email = email.value.trim() ? '' : t('common.emailRequired')
  return !errors.value.email
}

async function onSubmit() {
  if (!validate()) return
  isLoading.value = true
  errorMessage.value = ''
  errors.value.email = ''
  try {
    await usersApi.invite({ email: email.value.trim(), role_ids: selectedRoleIds.value })
    emit('update:open', false)
    emit('invited')
    toast({ title: t('users.invite.sent'), description: t('users.invite.sentDescription', { email: email.value.trim() }) })
  } catch (err: unknown) {
    const fieldErrors = resolveFieldErrors(err)
    if (fieldErrors['body__email']) {
      errors.value.email = fieldErrors['body__email']
    } else {
      errorMessage.value = resolveError(err)
    }
  } finally {
    isLoading.value = false
  }
}
</script>
