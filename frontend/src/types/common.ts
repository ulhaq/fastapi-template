export interface PaginatedResponse<T> {
  items: T[]
  page_number: number
  page_size: number
  total: number
}

export type SortParam = {
  key: string
  order: 'asc' | 'desc'
}

export interface FetchOptions {
  page: number
  itemsPerPage: number
  sortBy?: SortParam[]
  filterBy?: Record<string, string>
  search?: string
}
