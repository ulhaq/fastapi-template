import { ref, reactive, computed } from 'vue'
import { i18n } from '@/plugins/i18n'
import type { PaginatedResponse } from '@/types'

interface UseDataTableOptions<T> {
  fetcher: (params: {
    page_number: number
    page_size: number
    sort?: string
    filters?: string
  }) => Promise<{ data: PaginatedResponse<T> }>
  defaultPageSize?: number
  immediate?: boolean
}

export function useDataTable<T>(options: UseDataTableOptions<T>) {
  const { fetcher, defaultPageSize = 20, immediate = true } = options

  const items = ref<T[]>([])
  const total = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const pagination = reactive({ page: 1, pageSize: defaultPageSize })
  const currentSort = ref<string | undefined>(undefined)
  const currentFilters = ref<Record<string, { v: (string | number | boolean)[]; op: string }>>({})

  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pagination.pageSize)))

  async function fetchData() {
    isLoading.value = true
    error.value = null
    try {
      const filtersStr =
        Object.keys(currentFilters.value).length > 0
          ? JSON.stringify(currentFilters.value)
          : undefined
      const { data } = await fetcher({
        page_number: pagination.page,
        page_size: pagination.pageSize,
        sort: currentSort.value,
        filters: filtersStr,
      })
      if(data.items !== undefined){
        items.value = data.items
        total.value = data.total
      }
      else{
        items.value = data
      }
    } catch {
      error.value = i18n.global.t('common.failedToLoadData')
    } finally {
      isLoading.value = false
    }
  }

  function goToPage(page: number) {
    pagination.page = page
    fetchData()
  }

  function setPageSize(size: number) {
    pagination.pageSize = size
    pagination.page = 1
    fetchData()
  }

  function setSort(field: string, desc = false) {
    currentSort.value = field ? (desc ? `-${field}` : field) : undefined
    pagination.page = 1
    fetchData()
  }

  function setFilter(field: string, value: (string | number | boolean)[], op = 'ico') {
    if (value.length === 0) {
      delete currentFilters.value[field]
    } else {
      currentFilters.value[field] = { v: value, op }
    }
    pagination.page = 1
    fetchData()
  }

  function refresh() {
    fetchData()
  }

  if (immediate) {
    fetchData()
  }

  return {
    items,
    total,
    isLoading,
    error,
    pagination,
    totalPages,
    fetchData,
    goToPage,
    setPageSize,
    setSort,
    setFilter,
    refresh,
  }
}
