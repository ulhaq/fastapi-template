<route lang="yaml">
meta:
  breadcrumb: admin.organizations
</route>

<template>
  <div class="animate-fade-in">
    <PageHeader
      :title="$t('admin.organizations')"
      :description="$t('admin.organizationsDescription')"
    >
      <template #actions>
        <Button size="sm" @click="openCreate">
          <Plus class="w-4 h-4 mr-2" />
          {{ $t('admin.createOrganization') }}
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
      :empty-title="$t('admin.noOrganizations')"
      @sort="setSort"
      @update:page="goToPage"
      @update:page-size="setPageSize"
    >
      <template #toolbar>
        <Input
          v-model="searchQuery"
          placeholder="Search by name…"
          class="max-w-xs h-9"
          @input="handleSearch"
        />
        <Button v-if="searchQuery" variant="ghost" size="sm" @click="clearSearch">
          <X class="w-4 h-4" />
        </Button>
      </template>
      <template #row="{ item }">
        <TableCell class="font-medium">{{ item.name }}</TableCell>
        <TableCell class="text-muted-foreground text-xs">
          {{ formatDate(item.created_at) }}
        </TableCell>
        <TableCell>{{ item.plan_name ?? '—' }}</TableCell>
        <TableCell>
          <Badge
            v-if="item.subscription_status"
            variant="outline"
            :class="statusBadgeClass(item.subscription_status)"
          >
            {{ $t(`subscription.status.${item.subscription_status}`) }}
          </Badge>
          <span v-else class="text-muted-foreground">—</span>
        </TableCell>
      </template>
      <template #actions="{ item }">
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" size="sm" class="h-7 w-7 p-0">
              <MoreHorizontal class="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem class="cursor-pointer" @click="openEdit(item)">
              <Pencil class="w-4 h-4 mr-2" />
              {{ $t('common.edit') }}
            </DropdownMenuItem>
            <DropdownMenuItem class="cursor-pointer" @click="openMembers(item)">
              <Users class="w-4 h-4 mr-2" />
              {{ $t('admin.manageMembers') }}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              class="cursor-pointer text-destructive focus:text-destructive"
              @click="handleDelete(item)"
            >
              <Trash2 class="w-4 h-4 mr-2" />
              {{ $t('common.delete') }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </template>
    </DataTable>

    <AdminOrganizationForm v-model:open="showForm" :organization="selectedOrg" @saved="refresh" />
    <AdminOrgMembersDialog v-model:open="showMembers" :organization="selectedOrg" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { X, MoreHorizontal, Pencil, Trash2, Plus, Users } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { TableCell } from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import AdminOrganizationForm from '@/components/admin/AdminOrganizationForm.vue'
import AdminOrgMembersDialog from '@/components/admin/AdminOrgMembersDialog.vue'
import { adminApi } from '@/api/admin'
import { useDataTable } from '@/composables/useDataTable'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import type { AdminOrganizationOut } from '@/types'

const { t } = useI18n()
const { confirm } = useConfirm()
const { toast } = useToast()

const columns = [
  { key: 'name', label: t('common.name'), sortable: true },
  { key: 'created_at', label: t('common.created'), sortable: true },
  { key: 'plan_name', label: t('admin.columns.plan') },
  { key: 'subscription_status', label: t('admin.columns.status') },
]

const {
  items,
  total,
  isLoading,
  totalPages,
  pagination,
  goToPage,
  setPageSize,
  setSort,
  setFilter,
  refresh,
} = useDataTable<AdminOrganizationOut>({ fetcher: adminApi.listOrganizations })

const searchQuery = ref('')
let searchTimeout: ReturnType<typeof setTimeout>

function handleSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    setFilter('name', searchQuery.value ? [searchQuery.value] : [], 'ico')
  }, 300)
}

function clearSearch() {
  searchQuery.value = ''
  setFilter('name', [], 'ico')
}

const showForm = ref(false)
const showMembers = ref(false)
const selectedOrg = ref<AdminOrganizationOut | null>(null)

function openCreate() {
  selectedOrg.value = null
  showForm.value = true
}

function openEdit(org: AdminOrganizationOut) {
  selectedOrg.value = org
  showForm.value = true
}

function openMembers(org: AdminOrganizationOut) {
  selectedOrg.value = org
  showMembers.value = true
}

async function handleDelete(org: AdminOrganizationOut) {
  const ok = await confirm(
    t('admin.deleteOrgTitle'),
    t('admin.deleteOrgDescription', { name: org.name }),
    t('common.delete'),
  )
  if (!ok) return
  try {
    await adminApi.deleteOrganization(org.id)
    toast({ title: t('admin.orgDeleted') })
    refresh()
  } catch {
    toast({ title: t('admin.orgDeleteFailed'), variant: 'destructive' })
  }
}

function statusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    active: 'bg-green-100 text-green-800 border-green-200',
    trialing: 'bg-blue-100 text-blue-800 border-blue-200',
    past_due: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    canceled: 'bg-gray-100 text-gray-600 border-gray-200',
    incomplete: 'bg-red-100 text-red-600 border-red-200',
    paused: 'bg-orange-100 text-orange-800 border-orange-200',
  }
  return map[status] ?? ''
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
</script>
