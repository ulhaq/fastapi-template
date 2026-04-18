import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usersApi } from '@/api/users'
import type { TenantOut } from '@/types'

export const useTenancyStore = defineStore('tenancy', () => {
  const tenants = ref<TenantOut[]>([])

  async function fetchTenants(): Promise<void> {
    const { data } = await usersApi.getMyTenants()
    tenants.value = data
  }

  function clear(): void {
    tenants.value = []
  }

  return { tenants, fetchTenants, clear }
})
