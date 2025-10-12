import { defineStore } from "pinia";
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { useMessageStore } from "@/stores/message";
import roleApi from "@/apis/roles";
import utils from "@/utils";

export const useRoleStore = defineStore("role", () => {
  const { t } = useI18n();
  const messageStore = useMessageStore();

  const loading = ref(false);

  const roles = ref({
    items: [],
    page_number: 1,
    page_size: 10,
    total: 0,
  });
  const role = ref({
    id: "",
    name: "",
    description: "",
    permissions: [],
  });

  async function fetchRoles(options: any) {
    loading.value = true;

    roles.value = await roleApi.getAll({
      page_number: options.page,
      page_size: options.itemsPerPage,
      sort: utils.createSorts(options.sortBy),
      filters: utils.createFilters(options.filterBy, options.search),
    });

    loading.value = false;
  }

  async function createRole(role) {
    loading.value = true;

    try {
      const rs = await roleApi.create({
        name: role.name,
        description: role.description,
      });

      roles.value.items = [rs, ...roles.value.items];

      messageStore.add({
        text: t("roles.form.addSuccess", { name: "Role" }),
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

  async function updateRole(role) {
    loading.value = true;

    try {
      const rs = await roleApi.updateById(role.id, role);

      roles.value.items = roles.value.items.map((item) =>
        item.id === role.id ? rs : item
      );

      messageStore.add({
        text: t("roles.form.updateSuccess", { name: "Role" }),
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

  async function managePermissions(id, permissionIds) {
    try {
      const rs = await roleApi.managePermissions(id, permissionIds);

      roles.value.items = roles.value.items.map((item) =>
        item.id === id ? rs : item
      );

      messageStore.add({
        text: t("roles.form.assignedPermissionsSuccess"),
        color: "success",
      });

      return rs;
    } catch (err) {
      messageStore.add({
        text: err?.response?.data?.msg || t("errors.common"),
        color: "error",
      });

      throw err;
    }
  }

  async function deleteRole(id: string | number) {
    loading.value = true;

    try {
      await roleApi.deleteById(id);

      roles.value.items = roles.value.items.filter((item) => item.id !== id);
      roles.value.total -= 1;

      messageStore.add({
        text: t("roles.form.deleteSuccess", { name: "Role" }),
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

  const setRole = (newRole) => {
    role.value = newRole;
  };

  const resetRole = () => {
    role.value = {
      id: "",
      name: "",
      description: "",
      permissions: [],
    };
  };

  return {
    loading,
    roles,
    role,
    fetchRoles,
    createRole,
    updateRole,
    managePermissions,
    deleteRole,
    setRole,
    resetRole,
  };
});
