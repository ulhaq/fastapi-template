import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usersApi } from '@/api/users'
import type { UserOut } from '@/types'

export const useProfileStore = defineStore('profile', () => {
  const user = ref<UserOut | null>(null)
  const permissions = ref<string[]>([])

  function hasPermission(permission: string): boolean {
    return permissions.value.includes(permission)
  }

  async function fetchMe(): Promise<void> {
    const { data } = await usersApi.getMe()
    user.value = data
    permissions.value = [...new Set(data.roles.flatMap((r) => r.permissions.map((p) => p.name)))]
  }

  function clear(): void {
    user.value = null
    permissions.value = []
  }

  return { user, permissions, hasPermission, fetchMe, clear }
})
