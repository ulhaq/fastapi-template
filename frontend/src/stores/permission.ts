import { defineStore } from "pinia";
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { useMessageStore } from "@/stores/message";
import permissionApi from "@/apis/permissions";
import utils from "@/utils";

export const usePermissionStore = defineStore("permission", () => {
  const { t } = useI18n();
  const messageStore = useMessageStore();

  const loading = ref(false);

  const permissions = ref({
    items: [],
    page_number: 1,
    page_size: 10,
    total: 0,
  });
  const permission = ref({
    id: "",
    name: "",
    description: "",
  });

  async function fetchPermissions(options: any) {
    loading.value = true;

    permissions.value = await permissionApi.getAll({
      page_number: options.page,
      page_size: options.itemsPerPage,
      sort: utils.createSorts(options.sortBy),
      filters: utils.createFilters(options.filterBy, options.search),
    });

    loading.value = false;
  }

  async function createPermission(permission) {
    loading.value = true;

    try {
      const rs = await permissionApi.create({
        name: permission.name,
        description: permission.description,
      });

      permissions.value.items = [rs, ...permissions.value.items];

      messageStore.add({
        text: t("common.addSuccess", { name: "Permission" }),
        color: "success",
      });

      return rs;
    } catch (err) {
      messageStore.add({
        text: err.response?.data?.msg || t("errors.common"),
        color: "error",
      });

      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updatePermission(permission) {
    loading.value = true;

    try {
      const rs = await permissionApi.updateById(permission.id, permission);

      permissions.value.items = permissions.value.items.map((item) =>
        item.id === permission.id ? rs : item
      );

      messageStore.add({
        text: t("common.updateSuccess", { name: "Permission" }),
        color: "success",
      });

      return rs;
    } catch (err) {
      messageStore.add({
        text: err.response?.data?.msg || t("errors.common"),
        color: "error",
      });

      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deletePermission(id: string | number) {
    loading.value = true;

    try {
      await permissionApi.deleteById(id);

      permissions.value.items = permissions.value.items.filter(
        (item) => item.id !== id
      );
      permissions.value.total -= 1;

      messageStore.add({
        text: t("common.deleteSuccess", { name: "Permission" }),
        color: "success",
      });
    } catch (err) {
      messageStore.add({
        text: err.response?.data?.msg || t("errors.common"),
        color: "error",
      });

      throw err;
    } finally {
      loading.value = false;
    }
  }

  const setPermission = (newPermission) => {
    permission.value = newPermission;
  };

  const resetPermission = () => {
    permission.value = {
      id: "",
      name: "",
      description: "",
    };
  };

  return {
    loading,
    permissions,
    permission,
    fetchPermissions,
    createPermission,
    updatePermission,
    deletePermission,
    setPermission,
    resetPermission,
  };
});
