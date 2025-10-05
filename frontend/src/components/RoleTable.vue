<template>
  <data-table
    :headers="headers"
    :items="items"
    :total-items="totalItems"
    :loading="loading"
    :options="options"
    :selectedItems="selectedItems"
    show-select
    @update:options="fetchRoles"
  >
    <template #row-actions="{ item }">
      <v-btn
        class="me-2"
        icon
        variant="text"
        size="small"
        @click="$emit('editItem', item)"
      >
        <v-icon>mdi-pencil</v-icon>
      </v-btn>
      <v-menu
        v-model="deleteMenus[item.id]"
        offset-y
        :close-on-content-click="false"
      >
        <template #activator="{ props }">
          <v-btn v-bind="props" icon variant="text" size="small">
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
import { useI18n } from "vue-i18n";
import { ref, computed, watch } from "vue";
import { useMessageStore } from "@/stores/message";
import DataTable from "@/components/DataTable.vue";
import roleApi from "@/apis/roles";
import utils from "@/utils";

const props = defineProps({
  search: {
    type: String,
    required: false,
    default: "",
  },
});

defineEmits(["editItem"]);

const { t } = useI18n();

const headers = computed(() => [
  { title: t("common.name"), key: "name" },
  { title: t("common.description"), key: "description" },
  { title: t("common.createdAt"), key: "created_at" },
  { title: t("common.updatedAt"), key: "updated_at" },
  { title: t("common.actions"), key: "actions", sortable: false },
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

const messagesStore = useMessageStore();
const deleteMenus = ref({});

const fetchRoles = async (newOptions) => {
  options.value = newOptions;
  loading.value = true;

  const roles = await roleApi.getAll({
    page_number: newOptions.page,
    page_size: newOptions.itemsPerPage,
    sort: newOptions.sortBy,
    filters: utils.createFilters(
      { name: "co", description: "co" },
      props.search
    ),
  });

  items.value = roles.items;
  totalItems.value = roles.total;
  loading.value = false;
};

const confirmDelete = async (item) => {
  deleteMenus.value[item.id] = false;
  await roleApi.deleteById(item.id);
  messagesStore.add({
    text: t("common.deleteSuccess", { name: "Role" }),
    color: "success",
  });
  fetchRoles(options.value);
};

watch(
  () => props.search,
  () => {
    fetchRoles({ ...options.value, page: 1 });
  }
);
</script>
