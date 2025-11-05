<template>
  <v-container>
    <v-row justify="center">
      <v-col>
        <data-table
          v-model="selectedItems"
          :headers="headers"
          item-value="id"
          :items="items"
          :loading="loading"
          :options="options"
          show-select
          :total-items="totalItems"
          @update:options="fetchUsers"
        >
          <template #top>
            <v-toolbar flat>
              <v-toolbar-title>{{ t('users.title') }}</v-toolbar-title>
              <v-spacer />
              <v-text-field
                v-model="search"
                clearable
                hide-details
                :label="t('common.search')"
                variant="underlined"
              />
            </v-toolbar>
          </template>
        </data-table>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import roleApi from '@/apis/roles'
import DataTable from '@/components/DataTable.vue'

const { t } = useI18n()

const search = ref('')

const headers = computed(() => [
  { title: t('common.name'), key: 'name' },
  { title: t('common.description'), key: 'description' },
  { title: t('common.createdAt'), key: 'created_at' },
  { title: t('common.updatedAt'), key: 'updated_at' },
])

const items = ref([])
const selectedItems = ref([])
const totalItems = ref(0)
const loading = ref(false)

const options = ref({
  page: 1,
  itemsPerPage: 10,
  sortBy: [],
})

async function fetchUsers(newOptions) {
  options.value = newOptions
  loading.value = true

  const users = await roleApi.getAll({
    page_number: newOptions.page,
    page_size: newOptions.itemsPerPage,
    sort: newOptions.sortBy,
  })

  items.value = users.items
  totalItems.value = users.total
  loading.value = false
}

watch(search, () => {
  fetchUsers({ ...options.value, page: 1 })
})
</script>
