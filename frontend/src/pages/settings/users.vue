<route lang="yaml">
meta:
  permission: read:user
  breadcrumb: nav.users
</route>

<template>
  <div class="animate-fade-in">
    <PageHeader :title="$t('users.title')" :description="$t('users.description')">
      <template #actions>
        <PermissionGuard permission="create:user">
          <Button size="sm" @click="openInvite">
            <Mail class="w-4 h-4 mr-2" />
            {{ $t('users.invite.button') }}
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
      :empty-title="$t('users.noUsersFound')"
      :empty-description="$t('users.createFirstUser')"
      @sort="setSort"
      @update:page="goToPage"
      @update:page-size="setPageSize"
    >
      <template #toolbar>
        <Input
          v-model="searchQuery"
          :placeholder="$t('users.searchPlaceholder')"
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
            <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <span class="text-xs font-medium text-primary">{{ initials(item.name) }}</span>
            </div>
            <div>
              <p class="font-medium text-sm">{{ item.name }}</p>
              <p class="text-xs text-muted-foreground">{{ item.email }}</p>
            </div>
          </div>
        </TableCell>
        <TableCell>
          <div class="flex flex-wrap gap-1">
            <Badge
              v-for="role in item.roles.slice(0, 3)"
              :key="role.id"
              variant="secondary"
              class="text-xs"
            >
              {{ role.name }}
            </Badge>
            <Badge v-if="item.roles.length > 3" variant="outline" class="text-xs">
              +{{ item.roles.length - 3 }}
            </Badge>
          </div>
        </TableCell>
        <TableCell class="text-muted-foreground text-xs">
          {{ formatDate(item.created_at) }}
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
            <PermissionGuard permission="update:user">
              <DropdownMenuItem @click="openEdit(item)" class="cursor-pointer">
                <Pencil class="w-4 h-4 mr-2" />
                {{ $t('common.edit') }}
              </DropdownMenuItem>
            </PermissionGuard>
            <PermissionGuard permission="manage:user_role">
              <DropdownMenuItem @click="openRoles(item)" class="cursor-pointer">
                <Shield class="w-4 h-4 mr-2" />
                {{ $t('users.manageRoles') }}
              </DropdownMenuItem>
            </PermissionGuard>
            <PermissionGuard permission="delete:user">
              <DropdownMenuSeparator />
              <DropdownMenuItem
                @click="handleDelete(item)"
                class="cursor-pointer text-destructive focus:text-destructive"
              >
                <Trash2 class="w-4 h-4 mr-2" />
                {{ $t('common.delete') }}
              </DropdownMenuItem>
            </PermissionGuard>
          </DropdownMenuContent>
        </DropdownMenu>
      </template>
    </DataTable>

    <UserForm
      v-model:open="showForm"
      :user="selectedUser"
      @saved="refresh"
    />
    <UserRoleDialog
      v-model:open="showRoles"
      :user="selectedUser"
      @saved="refresh"
    />
    <InviteUserDialog
      v-model:open="showInvite"
      @invited="refresh"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Mail, MoreHorizontal, Pencil, Trash2, Shield, X } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { TableCell } from '@/components/ui/table'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import PermissionGuard from '@/components/common/PermissionGuard.vue'
import UserForm from '@/components/users/UserForm.vue'
import UserRoleDialog from '@/components/users/UserRoleDialog.vue'
import InviteUserDialog from '@/components/users/InviteUserDialog.vue'
import { usersApi } from '@/api/users'
import { useDataTable } from '@/composables/useDataTable'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import type { UserOut } from '@/types'

const { t } = useI18n()
const { toast } = useToast()
const { confirm } = useConfirm()

const columns = [
  { key: 'name', label: t('users.columns.user'), sortable: true },
  { key: 'roles', label: t('users.columns.roles') },
  { key: 'created_at', label: t('users.columns.created'), sortable: true },
]

const { items, total, isLoading, totalPages, pagination, goToPage, setPageSize, setSort, setFilter, refresh } =
  useDataTable<UserOut>({ fetcher: usersApi.list })

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
const showRoles = ref(false)
const showInvite = ref(false)
const selectedUser = ref<UserOut | null>(null)

function openInvite() {
  showInvite.value = true
}

function openEdit(user: UserOut) {
  selectedUser.value = user
  showForm.value = true
}

function openRoles(user: UserOut) {
  selectedUser.value = user
  showRoles.value = true
}

async function handleDelete(user: UserOut) {
  const ok = await confirm(
    t('users.deleteTitle'),
    t('users.deleteDescription', { name: user.name }),
    t('common.delete'),
  )
  if (!ok) return
  try {
    await usersApi.removeFromOrganization(user.id)
    toast({ title: t('users.deleted') })
    refresh()
  } catch {
    toast({ title: t('users.deleteFailed'), variant: 'destructive' })
  }
}

function initials(name: string) {
  return name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>
