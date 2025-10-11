<template>
  <data-table
    :headers="headers"
    :items="items"
    :total-items="totalItems"
    :loading="loading"
    :options="options"
    item-value="id"
    show-select
    v-model="modelValue"
    @update:options="fetchPermissions"
  />
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref } from "vue";
import DataTable from "@/components/DataTable.vue";
import permissionApi from "@/apis/permissions";

const { t } = useI18n();

const modelValue = ref();

const headers = computed(() => [
  { title: t("common.name"), key: "name" },
  { title: t("common.description"), key: "description" },
]);

const items = ref([]);
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
  });

  items.value = permissions.items;
  totalItems.value = permissions.total;
  loading.value = false;
};
</script>
