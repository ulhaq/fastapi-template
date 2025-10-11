<template>
  <data-table
    :headers="headers"
    :items="roleStore.roles.items"
    :total-items="roleStore.roles.total"
    :selected-items="selectedItems"
    :loading="roleStore.loading"
    :options="options"
    show-select
    @update:options="fetchRoles"
  >
    <template #toolbar-action>
      <role-form />
    </template>

    <template #row-actions="{ item }">
      <v-btn
        class="me-2"
        icon
        variant="text"
        size="small"
        @click="editRole(item)"
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
import { useRoleStore } from "@/stores/role";
import DataTable from "@/components/DataTable.vue";
import RoleForm from "@/components/roles/RoleForm.vue";

const roleStore = useRoleStore();

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

const fetchRoles = async (newOptions) => {
  options.value = newOptions;

  await roleStore.fetchRoles(newOptions);
};

const editRole = (role) => {
  roleStore.role = role;
};

const confirmDelete = async (item) => {
  deleteMenus.value[item.id] = false;

  await roleStore.deleteRole(item.id);
};
</script>
