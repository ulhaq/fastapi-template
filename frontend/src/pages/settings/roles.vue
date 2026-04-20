<route lang="yaml">
meta:
  permission: read:role
  breadcrumb: nav.roles
</route>

<template>
  <div class="animate-fade-in">
    <PageHeader :title="$t('roles.title')" :description="$t('roles.description')">
      <template #actions>
        <PermissionGuard permission="create:role">
          <Button size="sm" @click="openCreate">
            <Plus class="w-4 h-4 mr-2" />
            {{ $t('roles.addRole') }}
          </Button>
        </PermissionGuard>
      </template>
    </PageHeader>

    <DataTable
      :columns="columns"
      :items="items"
      :total="total"
      :page="pagination.page"
      :page-size="pagination.pageSize"
      :total-pages="totalPages"
      :loading="isLoading"
      :empty-title="$t('roles.noRolesFound')"
      :empty-description="$t('roles.createFirstRole')"
      @sort="setSort"
      @update:page="goToPage"
      @update:page-size="setPageSize"
    >
      <template #row="{ item }">
        <TableCell class="font-medium">
          {{ item.name }}
          <Badge v-if="item.is_protected" variant="secondary" class="text-xs ml-2">
            {{ $t('roles.protected') }}
          </Badge>
        </TableCell>
        <TableCell class="text-muted-foreground text-sm">
          {{ item.description || '-' }}
        </TableCell>
        <TableCell>
          <div class="flex flex-wrap gap-1">
            <Badge variant="outline" class="text-xs" v-for="p in item.permissions.slice(0, 4)" :key="p.id">
              {{ p.name }}
            </Badge>
            <Badge v-if="item.permissions.length > 4" variant="secondary" class="text-xs">
              +{{ item.permissions.length - 4 }}
            </Badge>
          </div>
        </TableCell>
        <TableCell class="text-muted-foreground text-xs">{{ formatDate(item.created_at) }}</TableCell>
      </template>
      <template #actions="{ item }">
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" size="sm" class="h-7 w-7 p-0">
              <MoreHorizontal class="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <template v-if="item.is_protected">
              <DropdownMenuItem @click="openPermissions(item, true)" class="cursor-pointer">
                <Key class="w-4 h-4 mr-2" />{{ $t('roles.viewPermissions') }}
              </DropdownMenuItem>
            </template>
            <template v-else>
              <PermissionGuard permission="update:role">
                <DropdownMenuItem @click="openEdit(item)" class="cursor-pointer">
                  <Pencil class="w-4 h-4 mr-2" />{{ $t('common.edit') }}
                </DropdownMenuItem>
              </PermissionGuard>
              <DropdownMenuItem v-if="hasPermission('manage:role_permission')" @click="openPermissions(item, false)" class="cursor-pointer">
                <Key class="w-4 h-4 mr-2" />{{ $t('roles.managePermissions') }}
              </DropdownMenuItem>
              <DropdownMenuItem v-else-if="hasPermission('read:permission')" @click="openPermissions(item, true)" class="cursor-pointer">
                <Key class="w-4 h-4 mr-2" />{{ $t('roles.viewPermissions') }}
              </DropdownMenuItem>
              <PermissionGuard permission="delete:role">
                <DropdownMenuSeparator />
                <DropdownMenuItem @click="handleDelete(item)" class="cursor-pointer text-destructive focus:text-destructive">
                  <Trash2 class="w-4 h-4 mr-2" />{{ $t('common.delete') }}
                </DropdownMenuItem>
              </PermissionGuard>
            </template>
          </DropdownMenuContent>
        </DropdownMenu>
      </template>
    </DataTable>

    <RoleForm v-model:open="showForm" :role="selectedRole" @saved="refresh" />
    <RolePermissionDialog v-model:open="showPerms" :role="selectedRole" :readonly="permsReadonly" @saved="refresh" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePermission } from '@/composables/usePermission'
import { Plus, MoreHorizontal, Pencil, Trash2, Key } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { TableCell } from '@/components/ui/table'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import PermissionGuard from '@/components/common/PermissionGuard.vue'
import RoleForm from '@/components/roles/RoleForm.vue'
import RolePermissionDialog from '@/components/roles/RolePermissionDialog.vue'
import { rolesApi } from '@/api/roles'
import { useDataTable } from '@/composables/useDataTable'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import type { RoleOut } from '@/types'

const { t } = useI18n()
const { toast } = useToast()
const { confirm } = useConfirm()
const { hasPermission } = usePermission()

const columns = [
  { key: 'name', label: t('roles.columns.name'), sortable: true },
  { key: 'description', label: t('roles.columns.description') },
  { key: 'permissions', label: t('roles.columns.permissions') },
  { key: 'created_at', label: t('roles.columns.created'), sortable: true },
]

const { items, total, isLoading, totalPages, pagination, goToPage, setPageSize, setSort, refresh } =
  useDataTable<RoleOut>({ fetcher: rolesApi.list })

const showForm = ref(false)
const showPerms = ref(false)
const permsReadonly = ref(false)
const selectedRole = ref<RoleOut | null>(null)

function openCreate() { selectedRole.value = null; showForm.value = true }
function openEdit(role: RoleOut) { selectedRole.value = role; showForm.value = true }
function openPermissions(role: RoleOut, readonly: boolean) { selectedRole.value = role; permsReadonly.value = readonly; showPerms.value = true }

async function handleDelete(role: RoleOut) {
  const ok = await confirm(
    t('roles.deleteTitle'),
    t('roles.deleteDescription', { name: role.name }),
    t('common.delete'),
  )
  if (!ok) return
  try {
    await rolesApi.delete(role.id)
    toast({ title: t('roles.deleted') })
    refresh()
  } catch {
    toast({ title: t('roles.deleteFailed'), variant: 'destructive' })
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>
