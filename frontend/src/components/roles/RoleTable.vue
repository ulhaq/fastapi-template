<template>
  <data-table
    v-model="selectedItems"
    :headers="headers"
    :items="roleStore.roles.items"
    :loading="roleStore.loading"
    :options="options"
    show-select
    :total-items="roleStore.roles.total"
    @update:options="fetchRoles"
  >
    <template #toolbar.action>
      <role-form />
    </template>

    <template #item.actions="{ item }">
      <v-btn
        class="me-2"
        icon
        size="small"
        variant="text"
        @click="editRole(item)"
      >
        <v-icon>mdi-pencil</v-icon>
      </v-btn>
      <v-menu v-model="deleteMenus[item.id]" :close-on-content-click="false">
        <template #activator="{ props }">
          <v-btn v-bind="props" icon size="small" variant="text">
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>

        <v-card>
          <v-card-actions>
            <v-btn variant="text" @click="deleteMenus[item.id] = false">{{
              t("common.cancel")
            }}</v-btn>
            <v-btn color="red" variant="text" @click="confirmDelete(item)">{{
              t("common.confirm")
            }}</v-btn>
          </v-card-actions>
        </v-card>
      </v-menu>
    </template>
  </data-table>
</template>

<script setup>
  import { computed, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import DataTable from '@/components/DataTable.vue'
  import RoleForm from '@/components/roles/RoleForm.vue'
  import { useRoleStore } from '@/stores/role'

  const roleStore = useRoleStore()

  const { t } = useI18n()

  const headers = computed(() => [
    { title: t('common.name'), key: 'name' },
    { title: t('common.description'), key: 'description' },
    { title: t('common.createdAt'), key: 'created_at' },
    { title: t('common.updatedAt'), key: 'updated_at' },
    { title: t('common.actions'), key: 'actions', sortable: false },
  ])

  const deleteMenus = ref({})
  const selectedItems = ref([])
  const options = ref({
    page: 1,
    itemsPerPage: 10,
    sortBy: [{ key: 'updated_at', order: 'desc' }],
    filterBy: { name: 'co', description: 'co' },
  })

  async function fetchRoles (newOptions) {
    options.value = newOptions

    await roleStore.fetchRoles(newOptions)
  }

  function editRole (role) {
    roleStore.role = role
  }

  async function confirmDelete (item) {
    deleteMenus.value[item.id] = false

    await roleStore.deleteRole(item.id)
  }
</script>
