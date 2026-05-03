<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-lg">
      <DialogHeader>
        <DialogTitle>{{ $t('admin.members') }} — {{ organization?.name }}</DialogTitle>
      </DialogHeader>

      <div class="space-y-4">
        <!-- Member list -->
        <div v-if="isLoading" class="flex justify-center py-4">
          <Loader2 class="w-5 h-5 animate-spin text-muted-foreground" />
        </div>
        <div v-else-if="members.length === 0" class="text-sm text-muted-foreground py-2">
          {{ $t('admin.noMembers') }}
        </div>
        <ul v-else class="divide-y divide-border rounded-md border">
          <li
            v-for="member in members"
            :key="member.user_id"
            class="flex items-center justify-between px-3 py-2"
          >
            <div>
              <p class="text-sm font-medium">{{ member.name }}</p>
              <p class="text-xs text-muted-foreground">{{ member.email }}</p>
              <div v-if="member.roles.length" class="flex flex-wrap gap-1 mt-1">
                <span
                  v-for="role in member.roles"
                  :key="role.id"
                  class="text-xs bg-muted px-1.5 py-0.5 rounded"
                >
                  {{ role.name }}
                </span>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              class="text-destructive hover:text-destructive"
              @click="handleRemove(member)"
            >
              <UserMinus class="w-4 h-4" />
            </Button>
          </li>
        </ul>

        <!-- Add member form -->
        <div class="border-t pt-4 space-y-2">
          <p class="text-sm font-medium">{{ $t('admin.addMember') }}</p>
          <div class="flex gap-2">
            <Input
              v-model="newEmail"
              type="email"
              :placeholder="$t('common.email')"
              :disabled="isAdding"
              class="flex-1"
              @keydown.enter.prevent="handleAdd"
            />
            <Button :disabled="isAdding || !newEmail" @click="handleAdd">
              <Loader2 v-if="isAdding" class="w-4 h-4 mr-2 animate-spin" />
              {{ $t('common.add') }}
            </Button>
          </div>
          <p v-if="addError" class="text-xs text-destructive">{{ addError }}</p>
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="$emit('update:open', false)">
          {{ $t('common.close') }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Loader2, UserMinus } from 'lucide-vue-next'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { adminApi } from '@/api/admin'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { useI18n } from 'vue-i18n'
import type { OrgMemberOut, OrganizationOut } from '@/types'

const props = defineProps<{ open: boolean; organization: OrganizationOut | null }>()
defineEmits<{ 'update:open': [boolean] }>()

const { t } = useI18n()
const { resolveError } = useErrorHandler()
const { confirm } = useConfirm()
const { toast } = useToast()

const members = ref<OrgMemberOut[]>([])
const isLoading = ref(false)
const newEmail = ref('')
const isAdding = ref(false)
const addError = ref('')

watch(
  () => props.open,
  (open) => {
    if (open && props.organization) {
      loadMembers()
      newEmail.value = ''
      addError.value = ''
    }
  },
)

async function loadMembers() {
  if (!props.organization) return
  isLoading.value = true
  try {
    const { data } = await adminApi.listOrgMembers(props.organization.id)
    members.value = data
  } finally {
    isLoading.value = false
  }
}

async function handleAdd() {
  if (!newEmail.value || !props.organization) return
  isAdding.value = true
  addError.value = ''
  try {
    const { data: member } = await adminApi.addOrgMember(props.organization.id, {
      email: newEmail.value,
    })
    members.value.push(member)
    newEmail.value = ''
    toast({ title: t('admin.memberAdded') })
  } catch (err: unknown) {
    addError.value = resolveError(err)
  } finally {
    isAdding.value = false
  }
}

async function handleRemove(member: OrgMemberOut) {
  if (!props.organization) return
  const ok = await confirm(
    t('admin.removeMemberTitle'),
    t('admin.removeMemberDescription', { name: member.name }),
    t('admin.removeMember'),
  )
  if (!ok) return
  try {
    await adminApi.removeOrgMember(props.organization.id, member.user_id)
    members.value = members.value.filter((m) => m.user_id !== member.user_id)
    toast({ title: t('admin.memberRemoved') })
  } catch (err: unknown) {
    toast({ title: resolveError(err), variant: 'destructive' })
  }
}
</script>
