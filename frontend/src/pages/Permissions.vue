<template>
  <v-container>
    <v-row justify="center">
      <v-col>
        <DataTable
          :headers="headers"
          :items="items"
          :total-items="totalItems"
          :loading="loading"
          :options="options"
          @update:options="fetchPermissions"
        >
          <template #top>
            <v-toolbar flat>
              <v-toolbar-title>{{ t("permissions.title") }}</v-toolbar-title>
              <v-spacer />
              <v-text-field
                v-model="search"
                :label="t('common.table.search')"
                hide-details
                clearable
                variant="underlined"
              />
            </v-toolbar>
          </template>

          <template #item="{ item }">
            <tr>
              <td>{{ item.name }}</td>
              <td>{{ item.description }}</td>
              <td>{{ item.created_at }}</td>
              <td>{{ item.updated_at }}</td>
            </tr>
          </template>
        </DataTable>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref, watch } from "vue";
import DataTable from "@/components/DataTable.vue";
import permissionApi from "@/apis/permissions";

const { t } = useI18n();

const headers = [
  { title: t("permissions.table.name"), key: "name" },
  { title: t("permissions.table.description"), key: "description" },
  { title: t("common.createdAt"), key: "createdAt" },
  { title: t("common.updatedAt"), key: "updatedAt" },
];

const items = ref([]);
const totalItems = ref(0);
const loading = ref(false);
const search = ref("");

const options = ref({
  page: 1,
  itemsPerPage: 10,
  sortBy: [],
});

const fetchPermissions = async (newOptions) => {
  options.value = newOptions;
  loading.value = true;

  const permissions = await permissionApi.getAll({
    page_number: newOptions.page,
    page_size: newOptions.itemsPerPage,
    sort: newOptions.sortBy,
  });

  items.value = permissions.items;
  totalItems.value = permissions.total;
  loading.value = false;
};

watch(search, () => {
  fetchPermissions({ ...options.value, page: 1 });
});
</script>
