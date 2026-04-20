<route lang="yaml">
meta:
  layout: dashboard
  requiresAuth: true
  breadcrumb: nav.dashboard
</route>

<template>
  <div class="animate-fade-in">
    <PageHeader :title="$t('dashboard.title')" :description="$t('dashboard.description')" />

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        :label="$t('dashboard.totalUsers')"
        :value="stats.users"
        :icon="Users"
        :loading="loading"
        icon-bg="bg-blue-50 dark:bg-blue-950"
        icon-color="text-blue-500"
      />
      <StatCard
        :label="$t('dashboard.organizations')"
        :value="stats.organizations"
        :icon="Building2"
        :loading="loading"
        icon-bg="bg-violet-50 dark:bg-violet-950"
        icon-color="text-violet-500"
      />
      <StatCard
        :label="$t('dashboard.roles')"
        :value="stats.roles"
        :icon="Shield"
        :loading="loading"
        icon-bg="bg-emerald-50 dark:bg-emerald-950"
        icon-color="text-emerald-500"
      />
      <StatCard
        :label="$t('dashboard.permissions')"
        :value="stats.permissions"
        :icon="Key"
        :loading="loading"
        icon-bg="bg-amber-50 dark:bg-amber-950"
        icon-color="text-amber-500"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Users, Building2, Shield, Key } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import { usersApi } from '@/api/users'
import { rolesApi } from '@/api/roles'
import { permissionsApi } from '@/api/permissions'
import { usePermission } from '@/composables/usePermission'
import type { OrganizationOut } from '@/types'

const { hasPermission } = usePermission()

const loading = ref(true)
const stats = ref<{ users: number | string; organizations: number | string; roles: number | string; permissions: number | string }>({ users: 0, organizations: 0, roles: 0, permissions: 0 })

onMounted(async () => {
  const requests = []
  if (hasPermission('read:user')) requests.push(usersApi.list({ page_size: 10 }))
  else requests.push(Promise.resolve({ data: { total: '-' } }))

  requests.push(usersApi.getMyOrganizations())

  if (hasPermission('read:role')) requests.push(rolesApi.list({ page_size: 10 }))
  else requests.push(Promise.resolve({ data: { total: '-' } }))

  if (hasPermission('read:permission')) requests.push(permissionsApi.list({ page_size: 10 }))
  else requests.push(Promise.resolve({ data: { total: '-' } }))

  const [users, organizations, roles, permissions] = await Promise.allSettled(requests)

  stats.value = {
    users: users.status === 'fulfilled' ? (users.value as { data: { total: number } }).data.total : '-',
    organizations: organizations.status === 'fulfilled' ? (organizations.value as { data: OrganizationOut[] }).data.length : '-',
    roles: roles.status === 'fulfilled' ? (roles.value as { data: { total: number } }).data.total : '-',
    permissions: permissions.status === 'fulfilled' ? (permissions.value as { data: { total: number } }).data.total : '-',
  }
  loading.value = false
})
</script>
