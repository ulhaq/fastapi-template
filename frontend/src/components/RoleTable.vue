<template>
  <DataTable
    :headers="headers"
    :items="items"
    :total-items="totalItems"
    :loading="loading"
    :options="options"
    :selectedItems="selectedItems"
    :item-value="id"
    show-select
    @update:options="fetchRoles"
  />
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref } from "vue";
import DataTable from "@/components/DataTable.vue";
import roleApi from "@/apis/roles";

const { t } = useI18n();

const headers = computed(() => [
  { title: t("roles.table.name"), key: "name" },
  { title: t("roles.table.description"), key: "description" },
  { title: t("common.table.createdAt"), key: "created_at" },
  { title: t("common.table.updatedAt"), key: "updated_at" },
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

const fetchRoles = async (newOptions) => {
  options.value = newOptions;
  loading.value = true;

  const roles = await roleApi.getAll({
    page_number: newOptions.page,
    page_size: newOptions.itemsPerPage,
    sort: newOptions.sortBy,
  });

  items.value = roles.items;
  totalItems.value = roles.total;
  loading.value = false;
};
</script>
