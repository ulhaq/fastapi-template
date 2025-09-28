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
        icon
        variant="text"
        size="small"
        @click="openPermissionsDialog(item)"
      >
        <v-icon>mdi-shield-star</v-icon>
      </v-btn>
      <v-btn
        class="me-2"
        icon
        variant="text"
        size="small"
        @click="editItem(item)"
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
            <v-btn variant="text" @click="deleteMenus[item.id] = false"
              >Cancel</v-btn
            >
            <v-btn color="red" variant="text" @click="confirmDelete(item)"
              >Confirm</v-btn
            >
          </v-card-actions>
        </v-card>
      </v-menu>
    </template>
  </data-table>

  <!-- Edit Dialog -->
  <v-dialog v-model="editDialog" max-width="600px">
    <v-card>
      <v-card-title>
        <span class="text-h6">{{ t("roles.editRole") }}</span>
      </v-card-title>

      <v-card-text>
        <v-form ref="editForm" v-model="formValid">
          <v-text-field
            v-model="editedItem.name"
            :label="t('roles.editForm.name')"
            :rules="[(v) => !!v || t('rules.required')]"
            required
          />
          <v-text-field
            v-model="editedItem.description"
            :label="t('roles.editForm.description')"
            :rules="[(v) => !!v || t('rules.required')]"
          />
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-btn
          color="error"
          :text="t('common.cancel')"
          size="large"
          variant="plain"
          @click="closeEditDialog"
        ></v-btn>
        <v-spacer />
        <v-btn
          color="white"
          :text="t('common.save')"
          size="large"
          variant="elevated"
          @click="saveEdit"
          :disabled="!formValid"
        />
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="permissionsDialog" max-width="600px">
    <v-card>
      <v-card-title>
        <span class="text-h6"
          >{{ t("roles.managePermissions") }} - {{ selectedRole?.name }}</span
        >
      </v-card-title>

      <v-card-text>
        <v-select
          v-model="selectedPermissions"
          :items="allPermissions"
          :label="t('roles.permissions')"
          item-title="name"
          item-value="id"
          multiple
          chips
        />
      </v-card-text>

      <v-card-actions>
        <v-btn
          color="error"
          :text="t('common.cancel')"
          size="large"
          variant="plain"
          @click="closePermissionsDialog"
        ></v-btn>
        <v-spacer></v-spacer>
        <v-btn
          color="white"
          :text="t('common.save')"
          size="large"
          variant="elevated"
          @click="savePermissions"
        ></v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useMessageStore } from "@/stores/message";
import DataTable from "@/components/DataTable.vue";
import roleApi from "@/apis/roles";
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
  { title: t("roles.table.name"), key: "name" },
  { title: t("roles.table.description"), key: "description" },
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

const messagesStore = useMessageStore();
const deleteMenus = ref({});

const editDialog = ref(false);
const editedItem = ref({});
const editForm = ref(null);
const formValid = ref(false);

const permissionsDialog = ref(false);
const selectedRole = ref(null);
const allPermissions = ref([]);
const selectedPermissions = ref([]);

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

const editItem = (item) => {
  editedItem.value = { ...item };
  editDialog.value = true;
};

const closeEditDialog = () => {
  editDialog.value = false;
  editedItem.value = {};
};

const saveEdit = async () => {
  const isValid = await editForm.value.validate();
  if (!isValid) return;

  try {
    await roleApi.updateById(editedItem.value.id, editedItem.value);
    messagesStore.add({ text: t("roles.updated"), color: "success" });
    editDialog.value = false;
    fetchRoles(options.value);
  } catch (err) {
    console.log(err);
    messagesStore.add({ text: t("common.error"), color: "error" });
  }
};

const confirmDelete = async (item) => {
  deleteMenus.value[item.id] = false;
  await roleApi.deleteById(item.id);
  messagesStore.add({ text: t("roles.deleted"), color: "success" });
  fetchRoles(options.value);
};

const openPermissionsDialog = async (role) => {
  selectedRole.value = role;
  permissionsDialog.value = true;

  try {
    if (allPermissions.value.length === 0) {
      const response = await permissionApi.getAll({ page_size: 100});
      allPermissions.value = response.items;
    }
    console.log(allPermissions);
    const response = await roleApi.getById(role.id);
    selectedPermissions.value = response.permissions;
  } catch (err) {
    console.log(err);
    messagesStore.add({ text: t("common.error"), color: "error" });
  }
};

const closePermissionsDialog = () => {
  permissionsDialog.value = false;
  selectedRole.value = null;
  selectedPermissions.value = [];
};

const savePermissions = async () => {
  try {
    await roleApi.managePermissions(
      selectedRole.value.id,
      selectedPermissions.value
    );
    messagesStore.add({
      text: t("roles.permissionsUpdated"),
      color: "success",
    });
    closePermissionsDialog();
  } catch (err) {
    console.log(err);
    messagesStore.add({ text: t("common.error"), color: "error" });
  }
};

watch(
  () => props.search,
  () => {
    fetchRoles({ ...options.value, page: 1 });
  }
);
</script>
