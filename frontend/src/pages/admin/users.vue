<route lang="yaml">
meta:
  breadcrumb: admin.users
</route>

<template>
  <div class="animate-fade-in">
    <PageHeader :title="$t('admin.users')" :description="$t('admin.usersDescription')" />

    <DataTable
      :columns="columns"
      :items="items"
      :total="total"
      :page="pagination.page"
      :page-size="pagination.pageSize"
      :total-pages="totalPages"
      :loading="isLoading"
      :empty-title="$t('admin.noUsers')"
      @sort="setSort"
      @update:page="goToPage"
      @update:page-size="setPageSize"
    >
      <template #toolbar>
        <Input
          v-model="searchQuery"
          placeholder="Search by name or email…"
          class="max-w-xs h-9"
          @input="handleSearch"
        />
        <Button v-if="searchQuery" variant="ghost" size="sm" @click="clearSearch">
          <X class="w-4 h-4" />
        </Button>
      </template>
      <template #row="{ item }">
        <TableCell>
          <div class="flex items-center gap-3">
            <div
              class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0"
            >
              <span class="text-xs font-medium text-primary">{{ initials(item.name) }}</span>
            </div>
            <div>
              <p class="font-medium text-sm">{{ item.name }}</p>
              <p class="text-xs text-muted-foreground">{{ item.email }}</p>
            </div>
          </div>
        </TableCell>
        <TableCell class="text-muted-foreground text-xs">
          {{ formatDate(item.created_at) }}
        </TableCell>
        <TableCell>
          <div class="flex flex-wrap gap-1">
            <span
              v-for="org in item.organizations"
              :key="org.id"
              class="text-xs bg-muted px-1.5 py-0.5 rounded"
            >
              {{ org.name }}
            </span>
            <span v-if="item.organizations.length === 0" class="text-muted-foreground">—</span>
          </div>
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
            <DropdownMenuItem class="cursor-pointer" @click="handleForcePasswordReset(item)">
              <KeyRound class="w-4 h-4 mr-2" />
              {{ $t('admin.forcePasswordReset') }}
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

    <AdminUserForm v-model:open="showForm" :user="selectedUser" @saved="refresh" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { X, MoreHorizontal, Pencil, Trash2, KeyRound } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
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
import AdminUserForm from '@/components/admin/AdminUserForm.vue'
import { adminApi } from '@/api/admin'
import { useDataTable } from '@/composables/useDataTable'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import type { AdminUserOut } from '@/types'

const { t } = useI18n()
const { confirm } = useConfirm()
const { toast } = useToast()

const columns = [
  { key: 'name', label: t('users.columns.user'), sortable: true },
  { key: 'created_at', label: t('users.columns.created'), sortable: true },
  { key: 'organizations', label: t('admin.columns.organizations') },
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
} = useDataTable<AdminUserOut>({ fetcher: adminApi.listUsers })

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
const selectedUser = ref<AdminUserOut | null>(null)

function openEdit(user: AdminUserOut) {
  selectedUser.value = user
  showForm.value = true
}

async function handleDelete(user: AdminUserOut) {
  const ok = await confirm(
    t('admin.deleteUserTitle'),
    t('admin.deleteUserDescription', { name: user.name }),
    t('common.delete'),
  )
  if (!ok) return
  try {
    await adminApi.deleteUser(user.id)
    toast({ title: t('admin.userDeleted') })
    refresh()
  } catch {
    toast({ title: t('admin.userDeleteFailed'), variant: 'destructive' })
  }
}

async function handleForcePasswordReset(user: AdminUserOut) {
  const ok = await confirm(
    t('admin.forcePasswordResetTitle'),
    t('admin.forcePasswordResetDescription', { name: user.name }),
    t('admin.forcePasswordReset'),
  )
  if (!ok) return
  try {
    await adminApi.forcePasswordReset(user.id)
    toast({ title: t('admin.passwordResetSent') })
  } catch {
    toast({ title: t('admin.forcePasswordResetFailed'), variant: 'destructive' })
  }
}

function initials(name: string) {
  return name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
</script>
