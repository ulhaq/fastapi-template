<route lang="yaml">
meta:
  breadcrumb: nav.organizations
</route>

<template>
  <div class="animate-fade-in">
    <PageHeader :title="$t('organizations.title')" :description="$t('organizations.description')">
      <template #actions>
        <Button size="sm" @click="openCreate">
          <Plus class="w-4 h-4 mr-2" />
          {{ $t('organizations.createOrganization') }}
        </Button>
      </template>
    </PageHeader>

    <DataTable
      :columns="columns"
      :items="items"
      :total="total"
      :loading="isLoading"
      :empty-title="$t('organizations.noOrganizationsFound')"
      :empty-description="$t('organizations.createFirstOrganization')"
      :show-pagination="false"
      @sort="setSort"
    >
      <template #row="{ item }">
        <TableCell class="font-medium">{{ item.name }}</TableCell>
        <TableCell>
          <Badge :variant="item.is_owner ? 'default' : 'secondary'" class="text-xs">
            {{ getOrgRole(item) }}
          </Badge>
        </TableCell>
        <TableCell class="text-muted-foreground text-xs">{{ formatDate(item.created_at) }}</TableCell>
      </template>
      <template #actions="{ item }">
        <DropdownMenu v-if="hasAnyOrgAction(item)">
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" size="sm" class="h-7 w-7 p-0">
              <MoreHorizontal class="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <PermissionGuard permission="read:user">
              <DropdownMenuItem @click="openUsers(item)" class="cursor-pointer">
                <Users class="w-4 h-4 mr-2" />{{ $t('organizations.viewMembers') }}
              </DropdownMenuItem>
            </PermissionGuard>
            <template v-if="isActiveOrg(item.id)">
              <PermissionGuard permission="update:organization">
                <DropdownMenuItem @click="openEdit(item)" class="cursor-pointer">
                  <Pencil class="w-4 h-4 mr-2" />{{ $t('common.edit') }}
                </DropdownMenuItem>
              </PermissionGuard>
              <template v-if="isOwner">
                <DropdownMenuSeparator />
                <DropdownMenuItem @click="openTransferOwnership(item)" class="cursor-pointer">
                  <ArrowRightLeft class="w-4 h-4 mr-2" />{{ $t('organizations.transferOwnership') }}
                </DropdownMenuItem>
              </template>
              <PermissionGuard permission="delete:organization">
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

    <OrganizationForm v-model:open="showForm" :organization="selectedOrganization" @saved="refresh" />
    <OrganizationUsersDialog v-model:open="showUsers" :organization="selectedOrganization" />
    <TransferOwnershipDialog v-model:open="showTransfer" :organization="selectedOrganization" @saved="handleOwnershipTransferred" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, MoreHorizontal, Pencil, Trash2, Users, ArrowRightLeft } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { TableCell } from '@/components/ui/table'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import PermissionGuard from '@/components/common/PermissionGuard.vue'
import OrganizationForm from '@/components/organizations/OrganizationForm.vue'
import OrganizationUsersDialog from '@/components/organizations/OrganizationUsersDialog.vue'
import TransferOwnershipDialog from '@/components/organizations/TransferOwnershipDialog.vue'
import { organizationsApi } from '@/api/organizations'
import { usersApi } from '@/api/users'
import { useDataTable } from '@/composables/useDataTable'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useProfileStore } from '@/stores/profile'
import { useSessionStore } from '@/stores/session'
import { usePermission } from '@/composables/usePermission'
import { PAGE_SIZE } from '@/constants'
import type { OrganizationOut, PaginatedResponse } from '@/types'

const { t } = useI18n()
const { toast } = useToast()
const { confirm } = useConfirm()
const { handleError } = useErrorHandler()
const profile = useProfileStore()
const session = useSessionStore()
const { hasPermission, isOwner } = usePermission()

function isActiveOrg(orgId: number): boolean {
  return session.activeOrganizationId === orgId
}

function hasAnyOrgAction(item: OrganizationOut): boolean {
  const active = isActiveOrg(item.id)
  return hasPermission('read:user')
    || (active && hasPermission('update:organization'))
    || (active && isOwner.value)
    || (active && hasPermission('delete:organization'))
}

const columns = [
  { key: 'name', label: t('organizations.columns.name'), sortable: true },
  { key: 'role', label: t('organizations.columns.role') },
  { key: 'created_at', label: t('organizations.columns.created'), sortable: true },
]

function getOrgRole(item: OrganizationOut): string {
  return item.is_owner ? t('organizations.roleOwner') : t('organizations.roleMember')
}

async function fetchOrganizations() {
  const { data } = await usersApi.getMyOrganizations()
  return { data: { items: data, total: data.length, page_number: 1, page_size: data.length } as PaginatedResponse<OrganizationOut> }
}

const { items, total, isLoading, setSort, refresh } =
  useDataTable<OrganizationOut>({ fetcher: fetchOrganizations, defaultPageSize: PAGE_SIZE })

const showForm = ref(false)
const showUsers = ref(false)
const showTransfer = ref(false)
const selectedOrganization = ref<OrganizationOut | null>(null)

function openCreate() { selectedOrganization.value = null; showForm.value = true }
function openEdit(organization: OrganizationOut) { selectedOrganization.value = organization; showForm.value = true }
function openUsers(organization: OrganizationOut) { selectedOrganization.value = organization; showUsers.value = true }
function openTransferOwnership(organization: OrganizationOut) { selectedOrganization.value = organization; showTransfer.value = true }

async function handleOwnershipTransferred() {
  await profile.fetchMe()
  refresh()
}

async function handleDelete(organization: OrganizationOut) {
  const ok = await confirm(
    t('organizations.deleteTitle'),
    t('organizations.deleteDescription', { name: organization.name }),
    t('common.delete'),
  )
  if (!ok) return
  try {
    await organizationsApi.delete(organization.id)
    toast({ title: t('organizations.deleted') })
    refresh()
  } catch (err) {
    handleError(err)
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>
