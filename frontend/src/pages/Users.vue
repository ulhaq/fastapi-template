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
          :item-value="id"
          show-select
          v-model="selectedItems"
          @update:options="fetchUsers"
        >
          <template #top>
            <v-toolbar flat>
              <v-toolbar-title>{{ t("users.title") }}</v-toolbar-title>
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
        </DataTable>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref, watch } from "vue";
import DataTable from "@/components/DataTable.vue";
import roleApi from "@/apis/roles";

const { t } = useI18n();

const headers = computed(() => [
  { title: t("users.table.name"), key: "name" },
  { title: t("users.table.description"), key: "description" },
  { title: t("common.table.createdAt"), key: "created_at" },
  { title: t("common.table.updatedAt"), key: "updated_at" },
]);

const items = ref([]);
const selectedItems = ref([]);
const totalItems = ref(0);
const loading = ref(false);
const search = ref("");

const options = ref({
  page: 1,
  itemsPerPage: 10,
  sortBy: [],
});

const fetchUsers = async (newOptions) => {
  options.value = newOptions;
  loading.value = true;

  const users = await roleApi.getAll({
    page_number: newOptions.page,
    page_size: newOptions.itemsPerPage,
    sort: newOptions.sortBy,
  });

  items.value = users.items;
  totalItems.value = users.total;
  loading.value = false;
};

watch(search, () => {
  fetchUsers({ ...options.value, page: 1 });
});
</script>
