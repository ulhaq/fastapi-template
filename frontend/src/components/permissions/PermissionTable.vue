<template>
  <data-table
    :headers="headers"
    :items="permissionStore.permissions.items"
    :total-items="permissionStore.permissions.total"
    :selected-items="selectedItems"
    :loading="permissionStore.loading"
    :options="options"
    show-select
    @update:options="fetchPermissions"
  >
    <template #toolbar-action>
      <permission-form />
    </template>

    <template #row-actions="{ item }">
      <v-btn
        class="me-2"
        icon
        variant="text"
        size="small"
        @click="editPermission(item)"
      >
        <v-icon>mdi-pencil</v-icon>
      </v-btn>
      <v-menu v-model="deleteMenus[item.id]" :close-on-content-click="false">
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
import { ref, computed } from "vue";
import { usePermissionStore } from "@/stores/permission";
import DataTable from "@/components/DataTable.vue";
import PermissionForm from "@/components/permissions/PermissionForm.vue";

const permissionStore = usePermissionStore();

const { t } = useI18n();

const headers = computed(() => [
  { title: t("common.name"), key: "name" },
  { title: t("common.description"), key: "description" },
  { title: t("common.createdAt"), key: "created_at" },
  { title: t("common.updatedAt"), key: "updated_at" },
  { title: t("common.actions"), key: "actions", sortable: false },
]);

const deleteMenus = ref({});
const selectedItems = ref([]);
const options = ref({
  page: 1,
  itemsPerPage: 10,
  sortBy: [{ key: "updated_at", order: "desc" }],
  filterBy: { name: "co", description: "co" },
});

const fetchPermissions = async (newOptions) => {
  options.value = newOptions;

  await permissionStore.fetchPermissions(newOptions);
};

const editPermission = (permission) => {
  permissionStore.permission = permission;
};

const confirmDelete = async (item) => {
  deleteMenus.value[item.id] = false;

  await permissionStore.deletePermission(item.id);
};
</script>
