<route lang="yaml">
meta:
  breadcrumb: admin.auditLogs
</route>

<template>
  <div class="animate-fade-in">
    <PageHeader :title="$t('admin.auditLogs')" :description="$t('admin.auditLogsDescription')" />

    <DataTable
      :columns="columns"
      :items="items"
      :total="total"
      :page="pagination.page"
      :page-size="pagination.pageSize"
      :total-pages="totalPages"
      :loading="isLoading"
      :empty-title="$t('admin.noAuditLogs')"
      @sort="setSort"
      @update:page="goToPage"
      @update:page-size="setPageSize"
    >
      <template #row="{ item }">
        <TableCell>
          <Badge variant="secondary" class="text-xs font-mono">{{ item.action }}</Badge>
        </TableCell>
        <TableCell class="text-muted-foreground text-xs">
          {{ item.organization_id ?? '—' }}
        </TableCell>
        <TableCell class="text-muted-foreground text-xs">
          {{ item.user_id ?? '—' }}
        </TableCell>
        <TableCell class="text-muted-foreground text-xs">
          {{ item.resource_type ?? '—' }}
        </TableCell>
        <TableCell class="text-muted-foreground text-xs">
          {{ item.ip_address ?? '—' }}
        </TableCell>
        <TableCell class="text-muted-foreground text-xs">
          {{ formatDate(item.created_at) }}
        </TableCell>
      </template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { TableCell } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import { adminApi } from '@/api/admin'
import { useDataTable } from '@/composables/useDataTable'
import type { AuditLogOut } from '@/types'

const { t } = useI18n()

const columns = [
  { key: 'action', label: t('admin.columns.action') },
  { key: 'organization_id', label: t('admin.columns.organization') },
  { key: 'user_id', label: t('admin.columns.user') },
  { key: 'resource_type', label: t('admin.columns.resourceType') },
  { key: 'ip_address', label: t('admin.columns.ipAddress') },
  { key: 'created_at', label: t('common.created'), sortable: true },
]

const { items, total, isLoading, totalPages, pagination, goToPage, setPageSize, setSort } =
  useDataTable<AuditLogOut>({ fetcher: adminApi.listAuditLogs })

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
</script>
