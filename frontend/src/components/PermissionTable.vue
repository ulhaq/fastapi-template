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
  <v-dialog v-model="editDialog" max-width="600">
    <v-card>
      <v-card-title>
        <span class="text-h6">{{ t("permissions.editForm.title") }}</span>
      </v-card-title>

      <v-card-text>
        <v-form ref="editForm" v-model="formValid">
          <v-text-field
            v-model="editedItem.name"
            :label="t('common.name')"
            :rules="[validation.required]"
          />
          <v-text-field
            v-model="editedItem.description"
            :label="t('common.description')"
            :rules="[validation.required]"
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
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref } from "vue";
import { useMessageStore } from "@/stores/message";
import { validation } from "@/plugins/validation";
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

const editDialog = ref(false);
const editedItem = ref({});
const editForm = ref(null);
const formValid = ref(false);

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
    await permissionApi.updateById(editedItem.value.id, editedItem.value);
    messagesStore.add({
      text: t("common.updateSuccess", { name: "Permission" }),
      color: "success",
    });
    editDialog.value = false;
    fetchPermissions(options.value);
  } catch (err) {
    console.log(err);
    messagesStore.add({ text: t("errors.common"), color: "error" });
  }
};

const confirmDelete = async (item) => {
  deleteMenus.value[item.id] = false;
  await permissionApi.deleteById(item.id);
  messagesStore.add({
    text: t("common.deleteSuccess", { name: "Permission" }),
    color: "success",
  });
  fetchPermissions(options.value);
};

watch(
  () => props.search,
  () => {
    fetchPermissions({ ...options.value, page: 1 });
  }
);
</script>
