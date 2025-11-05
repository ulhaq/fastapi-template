import type { FetchOptions, PaginatedResponse } from '@/types/common'
import type { Permission } from '@/types/permission'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import permissionApi from '@/apis/permissions'
import utils from '@/utils'

export const usePermissionStore = defineStore('permission', () => {
  const loading = ref(false)

  const permissions = ref<PaginatedResponse<Permission>>({
    items: [],
    page_number: 1,
    page_size: 10,
    total: 0,
  })

  const permission = ref<Permission>({
    id: 0,
    name: '',
    description: '',
  })

  async function fetchPermissions(options: FetchOptions) {
    loading.value = true
    try {
      permissions.value = await permissionApi.getAll({
        page_number: options.page,
        page_size: options.itemsPerPage,
        sort: utils.createSorts(options.sortBy),
        filters: utils.createFilters(options.filterBy, options.search),
      })
    } finally {
      loading.value = false
    }
  }

  async function createPermission(newPermission: Permission) {
    loading.value = true
    try {
      const rs = await permissionApi.create(newPermission)

      permissions.value.items = [rs, ...permissions.value.items]

      return rs
    } finally {
      loading.value = false
    }
  }

  async function updatePermission(updatedPermission: Permission) {
    loading.value = true
    try {
      const rs = await permissionApi.updateById(
        updatedPermission.id,
        updatedPermission,
      )

      permissions.value.items = permissions.value.items.map((item) =>
        item.id === updatedPermission.id ? rs : item,
      )

      return rs
    } finally {
      loading.value = false
    }
  }

  async function deletePermission(id: number) {
    loading.value = true
    try {
      await permissionApi.deleteById(id)

      permissions.value.items = permissions.value.items.filter(
        (item) => item.id !== id,
      )
      permissions.value.total = Math.max(0, permissions.value.total - 1)
    } finally {
      loading.value = false
    }
  }

  const setPermission = (newPermission: Permission) => {
    permission.value = newPermission
  }

  const resetPermission = () => {
    permission.value = { id: 0, name: '', description: '' }
  }

  return {
    loading,
    permissions,
    permission,
    fetchPermissions,
    createPermission,
    updatePermission,
    deletePermission,
    setPermission,
    resetPermission,
  }
})
