import type { SortParam } from '@/types/common'
import { isEmpty } from 'lodash'

function createSorts(params?: SortParam[] | null): string | null {
  if (isEmpty(params) || !params) {
    return null
  }

  return params
    .map(({ key, order }) => (order === 'desc' ? `-${key}` : key))
    .join(',')
}

function createFilters(
  params?: Record<string, string>,
  value?: string | null,
): string | null {
  if (!params || value == null || value === '') {
    return null
  }

  const filters = Object.fromEntries(
    Object.entries(params).map(([key, operator]) => [
      key,
      { v: [value], op: operator },
    ]),
  )

  return JSON.stringify(filters)
}

function highlightSearchTerm(searchTerm: string, text: string) {
  if (!searchTerm) {
    return text
  }

  const regex = new RegExp(`(?!<[^>]*?)(${searchTerm})(?![^<]*?>)`, 'gi')

  return String(text).replace(regex, '<strong>$1</strong>')
}

export default {
  createSorts,
  createFilters,
  highlightSearchTerm,
}
