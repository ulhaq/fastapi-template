<template>
  <data-table
    :headers="headers"
    :items="items"
    :total-items="totalItems"
    :loading="loading"
    :options="options"
    :selectedItems="selectedItems"
    show-select
    @update:options="fetchPermissions"
  >
    <template #row-actions="{ item }">
      <v-icon class="me-2" @click="editItem(item)">mdi-pencil</v-icon>
      <v-icon @click="deleteItem(item)">mdi-delete</v-icon>
    </template>
  </data-table>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref } from "vue";
import DataTable from "@/components/DataTable.vue";
import permissionApi from "@/apis/permissions";
import utils from "@/utils";

const props = defineProps({
  search: {
    type: String,
    required: false,
    default: "",
  },
});

const { t } = useI18n();

const headers = computed(() => [
  { title: t("permissions.table.name"), key: "name" },
  { title: t("permissions.table.description"), key: "description" },
  { title: t("common.table.createdAt"), key: "created_at" },
  { title: t("common.table.updatedAt"), key: "updated_at" },
  { title: t("common.table.actions"), key: "actions", sortable: false },
]);

const items = ref([]);
const selectedItems = ref([]);
const totalItems = ref(0);
const loading = ref(false);
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
    filters: utils.createFilters(
      { name: "co", description: "co" },
      props.search
    ),
  });

  items.value = permissions.items;
  totalItems.value = permissions.total;
  loading.value = false;
};

watch(
  () => props.search,
  () => {
    fetchPermissions({ ...options.value, page: 1 });
  }
);
</script>
