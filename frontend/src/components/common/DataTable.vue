<template>
  <div class="space-y-4">
    <!-- Toolbar slot -->
    <div v-if="$slots.toolbar" class="flex items-center gap-3">
      <slot name="toolbar" />
    </div>

    <!-- Table -->
    <div class="rounded-lg border border-border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow class="bg-muted/40 hover:bg-muted/40">
            <TableHead
              v-for="col in columns"
              :key="col.key"
              :class="[col.class, col.sortable && 'cursor-pointer select-none hover:text-foreground']"
              @click="col.sortable ? $emit('sort', col.key) : undefined"
            >
              <div class="flex items-center gap-1">
                {{ col.label }}
                <ArrowUpDown v-if="col.sortable" class="w-3.5 h-3.5 text-muted-foreground/60" />
              </div>
            </TableHead>
            <TableHead v-if="$slots.actions" class="w-20 text-right">{{ $t('common.actions') }}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <!-- Loading -->
          <template v-if="loading">
            <TableRow v-for="n in pageSize" :key="`skeleton-${n}`">
              <TableCell v-for="col in columns" :key="col.key">
                <Skeleton class="h-4 w-full max-w-[200px]" />
              </TableCell>
              <TableCell v-if="$slots.actions">
                <Skeleton class="h-4 w-16 ml-auto" />
              </TableCell>
            </TableRow>
          </template>
          <!-- Empty -->
          <template v-else-if="!items.length">
            <TableRow>
              <TableCell :colspan="columns.length + ($slots.actions ? 1 : 0)" class="h-52 p-0">
                <EmptyState :title="emptyTitle" :description="emptyDescription" />
              </TableCell>
            </TableRow>
          </template>
          <!-- Data -->
          <template v-else>
            <TableRow
              v-for="item in items"
              :key="(item as Record<string, unknown>)[rowKey] as string"
              class="hover:bg-muted/30 transition-colors"
            >
              <slot name="row" :item="item" />
              <TableCell v-if="$slots.actions" class="text-right">
                <slot name="actions" :item="item" />
              </TableCell>
            </TableRow>
          </template>
        </TableBody>
      </Table>
    </div>

    <!-- Pagination -->
    <DataTablePagination
      :total="total"
      :page="page"
      :page-size="pageSize"
      :total-pages="totalPages"
      @update:page="$emit('update:page', $event)"
      @update:page-size="$emit('update:pageSize', $event)"
    />
  </div>
</template>

<script setup lang="ts" generic="T">
import { useI18n } from 'vue-i18n'
import { ArrowUpDown } from 'lucide-vue-next'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import EmptyState from './EmptyState.vue'
import DataTablePagination from './DataTablePagination.vue'

useI18n()

export interface ColumnDef {
  key: string
  label: string
  sortable?: boolean
  class?: string
}

withDefaults(
  defineProps<{
    columns: ColumnDef[]
    items: T[]
    total: number
    page: number
    pageSize: number
    totalPages: number
    loading?: boolean
    rowKey?: string
    emptyTitle?: string
    emptyDescription?: string
  }>(),
  {
    rowKey: 'id',
  },
)

defineEmits<{
  sort: [field: string]
  'update:page': [page: number]
  'update:pageSize': [size: number]
}>()
</script>
