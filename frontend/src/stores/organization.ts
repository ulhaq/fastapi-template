import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usersApi } from '@/api/users'
import type { OrganizationOut } from '@/types'

export const useOrganizationStore = defineStore('organization', () => {
  const organizations = ref<OrganizationOut[]>([])

  async function fetchOrganizations(): Promise<void> {
    const { data } = await usersApi.getMyOrganizations()
    organizations.value = data
  }

  function clear(): void {
    organizations.value = []
  }

  return { organizations, fetchOrganizations, clear }
})
