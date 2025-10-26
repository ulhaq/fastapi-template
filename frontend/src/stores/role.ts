import type { FetchOptions, PaginatedResponse } from '@/types/common'
import type { Role } from '@/types/role'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import roleApi from '@/apis/roles'
import utils from '@/utils'

export const useRoleStore = defineStore('role', () => {
  const loading = ref(false)

  const roles = ref<PaginatedResponse<Role>>({
    items: [],
    page_number: 1,
    page_size: 10,
    total: 0,
  })

  const role = ref<Role | Role>({
    id: 0,
    name: '',
    description: '',
    permission_ids: [],
  })

  async function fetchRoles (options: FetchOptions) {
    loading.value = true
    try {
      roles.value = await roleApi.getAll({
        page_number: options.page,
        page_size: options.itemsPerPage,
        sort: utils.createSorts(options.sortBy),
        filters: utils.createFilters(options.filterBy, options.search),
      })
    } finally {
      loading.value = false
    }
  }

  async function createRole (newRole: Role) {
    loading.value = true
    try {
      const rs = await roleApi.create(newRole)

      roles.value.items = [rs, ...roles.value.items]

      return rs
    } finally {
      loading.value = false
    }
  }

  async function updateRole (updatedRole: Role) {
    loading.value = true
    try {
      const rs = await roleApi.updateById(updatedRole.id, updatedRole)

      roles.value.items = roles.value.items.map(item =>
        item.id === updatedRole.id ? rs : item,
      )

      return rs
    } finally {
      loading.value = false
    }
  }

  async function managePermissions (
    roleId: string | number,
    permissionIds: string[],
  ) {
    loading.value = true
    try {
      const rs = await roleApi.managePermissions(roleId, permissionIds)

      roles.value.items = roles.value.items.map(item =>
        item.id === roleId ? rs : item,
      )

      return rs
    } finally {
      loading.value = false
    }
  }

  async function deleteRole (id: number) {
    loading.value = true
    try {
      await roleApi.deleteById(id)

      roles.value.items = roles.value.items.filter(item => item.id !== id)
      roles.value.total = Math.max(0, roles.value.total - 1)
    } finally {
      loading.value = false
    }
  }

  const setRole = (newRole: Role) => {
    role.value = newRole
  }

  const resetRole = () => {
    role.value = { id: 0, name: '', description: '', permission_ids: [] }
  }

  return {
    loading,
    roles,
    role,
    fetchRoles,
    createRole,
    updateRole,
    managePermissions,
    deleteRole,
    setRole,
    resetRole,
  }
})
