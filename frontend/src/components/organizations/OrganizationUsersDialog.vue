<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ $t('organizations.usersDialog.title') }}</DialogTitle>
        <DialogDescription>{{ $t('organizations.usersDialog.description', { name: organization?.name }) }}</DialogDescription>
      </DialogHeader>

      <div v-if="loading" class="py-4 space-y-2">
        <Skeleton v-for="n in 3" :key="n" class="h-12 w-full" />
      </div>
      <div v-else class="space-y-1 max-h-72 overflow-y-auto py-1">
        <div
          v-for="user in users"
          :key="user.id"
          class="flex items-center justify-between px-3 py-2 rounded-md hover:bg-muted"
        >
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <span class="text-xs font-medium text-primary">{{ initials(user.name) }}</span>
            </div>
            <div>
              <p class="text-sm font-medium">{{ user.name }}</p>
              <p class="text-xs text-muted-foreground">{{ user.email }}</p>
            </div>
          </div>
          <PermissionGuard permission="manage:organization_user">
            <Button variant="ghost" size="sm" class="h-7 w-7 p-0 text-muted-foreground hover:text-destructive" @click="removeUser(user.id)">
              <X class="w-4 h-4" />
            </Button>
          </PermissionGuard>
        </div>
        <EmptyState
          v-if="!users.length"
          :title="$t('organizations.usersDialog.noMembers')"
          :description="$t('organizations.usersDialog.noUsers')"
        />
      </div>

      <DialogFooter>
        <Button variant="outline" @click="$emit('update:open', false)">{{ $t('common.close') }}</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { X } from 'lucide-vue-next'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from '@/components/common/EmptyState.vue'
import PermissionGuard from '@/components/common/PermissionGuard.vue'
import { organizationsApi } from '@/api/organizations'
import { usersApi } from '@/api/users'
import type { OrganizationOut, UserOut } from '@/types'
import { useToast } from '@/composables/useToast'

const props = defineProps<{ open: boolean; organization?: OrganizationOut | null }>()
defineEmits<{ 'update:open': [boolean] }>()

const { toast } = useToast()
const { t } = useI18n()
const users = ref<UserOut[]>([])
const loading = ref(false)

watch(() => props.open, async (open) => {
  if (!open || !props.organization) return
  loading.value = true
  try {
    const { data } = await organizationsApi.getUsers(props.organization.id)
    users.value = data.items
  } finally {
    loading.value = false
  }
})

async function removeUser(userId: number) {
  if (!props.organization) return
  try {
    await usersApi.removeFromOrganization(userId)
    users.value = users.value.filter((u) => u.id !== userId)
    toast({ title: t('organizations.usersDialog.userRemoved') })
  } catch {
    toast({ title: t('organizations.usersDialog.removeFailed'), variant: 'destructive' })
  }
}

function initials(name: string) {
  return name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
}
</script>
