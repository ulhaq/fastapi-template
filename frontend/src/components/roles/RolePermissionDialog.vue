<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ readonly ? $t('roles.viewPermissions') : $t('roles.permissionDialog.title') }}</DialogTitle>
        <DialogDescription>{{ readonly ? $t('roles.permissionDialog.viewDescription', { name: role?.name }) : $t('roles.permissionDialog.description', { name: role?.name }) }}</DialogDescription>
      </DialogHeader>

      <div v-if="loadingPerms" class="py-4 space-y-2">
        <Skeleton v-for="n in 4" :key="n" class="h-8 w-full" />
      </div>
      <div v-else class="space-y-1 max-h-72 overflow-y-auto py-1">
        <template v-for="(group, category) in grouped" :key="category">
          <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-1 mt-3 first:mt-0">
            {{ category }}
          </p>
          <div
            v-for="perm in group"
            :key="perm.id"
            :class="['flex items-center gap-3 px-2 py-1.5 rounded-md', readonly ? '' : 'hover:bg-muted cursor-pointer']"
            @click="!readonly && togglePerm(perm.id)"
          >
            <Checkbox
              :model-value="selectedIds.includes(perm.id)"
              :disabled="readonly"
              @click.stop="!readonly && togglePerm(perm.id)"
            />
            <div>
              <p class="text-sm font-medium">{{ perm.name }}</p>
              <p v-if="perm.description" class="text-xs text-muted-foreground">{{ perm.description }}</p>
            </div>
          </div>
        </template>
      </div>

      <DialogFooter>
        <Button v-if="readonly" @click="$emit('update:open', false)">{{ $t('common.close') }}</Button>
        <template v-else>
          <Button variant="outline" @click="$emit('update:open', false)" :disabled="isLoading">{{ $t('common.cancel') }}</Button>
          <Button @click="onSave" :disabled="isLoading">
            <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
            {{ $t('common.save') }}
          </Button>
        </template>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Skeleton } from '@/components/ui/skeleton'
import { permissionsApi } from '@/api/permissions'
import { rolesApi } from '@/api/roles'
import type { RoleOut, PermissionOut } from '@/types'
import { useToast } from '@/composables/useToast'

const props = defineProps<{ open: boolean; role?: RoleOut | null; readonly?: boolean }>()
const emit = defineEmits<{ 'update:open': [boolean]; saved: [] }>()

const { toast } = useToast()
const { t } = useI18n()
const allPerms = ref<PermissionOut[]>([])
const selectedIds = ref<number[]>([])
const loadingPerms = ref(false)
const isLoading = ref(false)

const grouped = computed(() => {
  const map: Record<string, PermissionOut[]> = {}
  for (const p of allPerms.value) {
    const cat = p.name.split(':')[1] ?? 'other'
    if (!map[cat]) map[cat] = []
    map[cat]!.push(p)
  }
  return map
})

watch(() => props.open, async (open) => {
  if (!open || !props.role) return
  loadingPerms.value = true
  try {
    const { data } = await permissionsApi.list({ page_size: 100 })
    allPerms.value = data.items
    selectedIds.value = props.role.permissions.map((p) => p.id)
  } finally {
    loadingPerms.value = false
  }
})

function togglePerm(id: number) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1)
  }
  else {
    selectedIds.value.push(id)
  }
}

async function onSave() {
  if (!props.role) return
  isLoading.value = true
  try {
    await rolesApi.setPermissions(props.role.id, { permission_ids: selectedIds.value })
    emit('update:open', false)
    emit('saved')
    toast({ title: t('roles.permissionDialog.saved') })
  } catch {
    toast({ title: t('roles.permissionDialog.saveFailed'), variant: 'destructive' })
  } finally {
    isLoading.value = false
  }
}
</script>
