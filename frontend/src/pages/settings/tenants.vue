<route lang="yaml">
meta:
  permission: read:tenant
  breadcrumb: nav.tenants
</route>

<template>
  <div class="animate-fade-in">
    <PageHeader :title="$t('tenants.title')" :description="$t('tenants.description')">
      <template #actions>
        <Button size="sm" @click="openCreate">
          <Plus class="w-4 h-4 mr-2" />
          {{ $t('tenants.addTenant') }}
        </Button>
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
      :empty-title="$t('tenants.noTenantsFound')"
      :empty-description="$t('tenants.createFirstTenant')"
      @sort="setSort"
      @update:page="goToPage"
      @update:page-size="setPageSize"
    >
      <template #row="{ item }">
        <TableCell class="font-medium">{{ item.name }}</TableCell>
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
            <DropdownMenuItem @click="openUsers(item)" class="cursor-pointer">
              <Users class="w-4 h-4 mr-2" />{{ $t('tenants.viewMembers') }}
            </DropdownMenuItem>
            <PermissionGuard permission="update:tenant">
              <DropdownMenuItem @click="openEdit(item)" class="cursor-pointer">
                <Pencil class="w-4 h-4 mr-2" />{{ $t('common.edit') }}
              </DropdownMenuItem>
            </PermissionGuard>
            <PermissionGuard permission="delete:tenant">
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="handleDelete(item)" class="cursor-pointer text-destructive focus:text-destructive">
                <Trash2 class="w-4 h-4 mr-2" />{{ $t('common.delete') }}
              </DropdownMenuItem>
            </PermissionGuard>
          </DropdownMenuContent>
        </DropdownMenu>
      </template>
    </DataTable>

    <TenantForm v-model:open="showForm" :tenant="selectedTenant" @saved="refresh" />
    <TenantUsersDialog v-model:open="showUsers" :tenant="selectedTenant" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, MoreHorizontal, Pencil, Trash2, Users } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { TableCell } from '@/components/ui/table'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import PermissionGuard from '@/components/common/PermissionGuard.vue'
import TenantForm from '@/components/tenants/TenantForm.vue'
import TenantUsersDialog from '@/components/tenants/TenantUsersDialog.vue'
import { tenantsApi } from '@/api/tenants'
import { usersApi } from '@/api/users'
import { useDataTable } from '@/composables/useDataTable'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import type { TenantOut } from '@/types'

const { t } = useI18n()
const { toast } = useToast()
const { confirm } = useConfirm()

const columns = [
  { key: 'name', label: t('tenants.columns.name'), sortable: true },
  { key: 'created_at', label: t('tenants.columns.created'), sortable: true },
]

const { items, total, isLoading, totalPages, pagination, goToPage, setPageSize, setSort, refresh } =
  useDataTable<TenantOut>({ fetcher: usersApi.getMyTenants })

const showForm = ref(false)
const showUsers = ref(false)
const selectedTenant = ref<TenantOut | null>(null)

function openCreate() { selectedTenant.value = null; showForm.value = true }
function openEdit(tenant: TenantOut) { selectedTenant.value = tenant; showForm.value = true }
function openUsers(tenant: TenantOut) { selectedTenant.value = tenant; showUsers.value = true }

async function handleDelete(tenant: TenantOut) {
  const ok = await confirm(
    t('tenants.deleteTitle'),
    t('tenants.deleteDescription', { name: tenant.name }),
    t('common.delete'),
  )
  if (!ok) return
  try {
    await tenantsApi.delete(tenant.id)
    toast({ title: t('tenants.deleted') })
    refresh()
  } catch {
    toast({ title: t('tenants.deleteFailed'), variant: 'destructive' })
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>
