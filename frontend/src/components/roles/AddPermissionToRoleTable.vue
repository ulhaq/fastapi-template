<template>
  <data-table
    v-model="modelValue"
    :headers="headers"
    item-value="id"
    :items="permissionStore.permissions.items"
    :loading="permissionStore.loading"
    :options="options"
    show-select
    :total-items="permissionStore.permissions.total"
    @update:options="fetchPermissions"
  />
</template>

<script setup>
  import { ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import DataTable from '@/components/DataTable.vue'
  import { usePermissionStore } from '@/stores/permission'

  const { t } = useI18n()

  const permissionStore = usePermissionStore()

  const modelValue = defineModel()

  const headers = computed(() => [
    { title: t('common.name'), key: 'name' },
    { title: t('common.description'), key: 'description' },
  ])

  const options = ref({
    page: 1,
    itemsPerPage: 10,
    sortBy: [{ key: 'updated_at', order: 'desc' }],
    filterBy: { name: 'co', description: 'co' },
  })

  async function fetchPermissions (newOptions) {
    try {
      options.value = newOptions

      await permissionStore.fetchPermissions(newOptions)
    } catch (error) {
      useErrorHandler(error)
    }
  }
</script>
