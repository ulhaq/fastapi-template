<template>
  <data-table
    v-model="selectedItems"
    :headers="headers"
    :items="permissionStore.permissions.items"
    :loading="permissionStore.loading"
    :options="options"
    show-select
    :toolbar-spacer="toolbarSpacer"
    :total-items="permissionStore.permissions.total"
    @update:options="fetchPermissions"
  >
    <template #toolbar.action>
      <slot v-if="$slots['toolbar.action']" name="toolbar.action" />
      <permission-form v-else />
    </template>

    <template #item.actions="{ item }">
      <v-btn
        class="me-2"
        icon
        size="small"
        variant="text"
        @click="editPermission(item)"
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
              t('common.cancel')
            }}</v-btn>
            <v-btn
              color="red"
              :loading="permissionStore.loading"
              variant="text"
              @click="confirmDelete(item)"
              >{{ t('common.confirm') }}</v-btn
            >
          </v-card-actions>
        </v-card>
      </v-menu>
    </template>
  </data-table>
</template>

<script setup>
import { isEmpty } from 'lodash'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import DataTable from '@/components/DataTable.vue'
import PermissionForm from '@/components/permissions/PermissionForm.vue'
import { useErrorHandler } from '@/composables/errorHandler'
import { useMessageStore } from '@/stores/message'
import { usePermissionStore } from '@/stores/permission'

const componentProps = defineProps({
  toolbarSpacer: {
    type: Boolean,
    default: true,
  },
  headers: {
    type: Array,
    default: () => [],
  },
})

const { t } = useI18n()
const messageStore = useMessageStore()
const permissionStore = usePermissionStore()

const headers = computed(() => {
  return isEmpty(componentProps.headers)
    ? [
        { title: t('common.name'), key: 'name' },
        { title: t('common.description'), key: 'description' },
        { title: t('common.createdAt'), key: 'created_at' },
        { title: t('common.updatedAt'), key: 'updated_at' },
        { title: t('common.actions'), key: 'actions', sortable: false },
      ]
    : componentProps.headers
})

const deleteMenus = ref({})
const selectedItems = ref([])
const options = ref({
  page: 1,
  itemsPerPage: 10,
  sortBy: [{ key: 'updated_at', order: 'desc' }],
  filterBy: {
    name: 'ico',
    description: 'ico',
    created_at: 'co',
    updated_at: 'co',
  },
})

async function fetchPermissions(newOptions) {
  options.value = newOptions

  try {
    await permissionStore.fetchPermissions(newOptions)
  } catch (error) {
    useErrorHandler(error)
  }
}

function editPermission(permission) {
  permissionStore.permission = permission
}

async function confirmDelete(item) {
  try {
    await permissionStore.deletePermission(item.id)

    deleteMenus.value[item.id] = false

    messageStore.add({
      text: t('permissions.form.deleteSuccess'),
      type: 'success',
    })
  } catch (error) {
    useErrorHandler(error)
  }
}
</script>
