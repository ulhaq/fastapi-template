<template>
  <v-btn color="white" size="large" variant="elevated" @click="openForm">
    {{ t("roles.add") }}
  </v-btn>
  <v-dialog v-model="open" max-width="768" persistent>
    <v-stepper
      :items="[t('roles.title'), t('permissions.title')]"
      v-model="step"
      hide-actions
      :editable="isEditing"
    >
      <template v-slot:item.1>
        <v-card>
          <v-card-title>
            <span class="text-h6">{{ title }}</span>
          </v-card-title>

          <v-card-text>
            <v-row>
              <v-col>
                <v-text-field
                  :label="t('common.name')"
                  v-model="role.name"
                  required
                ></v-text-field>
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <v-text-field
                  :label="t('common.description')"
                  v-model="role.description"
                  required
                ></v-text-field>
              </v-col>
            </v-row>
          </v-card-text>

          <v-card-actions>
            <v-btn
              color="error"
              :text="t('common.cancel')"
              size="large"
              variant="plain"
              @click="closeForm"
            ></v-btn>
            <v-spacer></v-spacer>
            <v-btn
              color="white"
              :text="t('roles.form.saveAndNext')"
              size="large"
              variant="elevated"
              :loading="loading"
              @click="addRoleAndNextStep"
            ></v-btn>
            <v-btn
              color="white"
              :text="t('common.save')"
              size="large"
              variant="elevated"
              @click="submit"
            ></v-btn>
          </v-card-actions>
        </v-card>
      </template>
      <template v-slot:item.2>
        <v-card>
          <v-card-title>
            <span class="text-h6">{{
              t("roles.form.assignPermissionsToRole")
            }}</span>
          </v-card-title>

          <v-card-text>
            <add-permission-to-role-table v-model="selectedPermissions" />
          </v-card-text>

          <v-card-actions>
            <v-btn
              color="error"
              :text="t('common.cancel')"
              size="large"
              variant="plain"
              @click="closeForm"
            ></v-btn>
            <v-spacer></v-spacer>
            <v-btn
              color="white"
              :text="t('roles.form.assignPermissionsToRole')"
              size="large"
              variant="elevated"
              @click="assignPermissionsToRole"
            ></v-btn>
          </v-card-actions>
        </v-card>
      </template>
    </v-stepper>
  </v-dialog>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref, computed, watch } from "vue";
import { useMessageStore } from "@/stores/message";
import { validation } from "@/plugins/validation";
import roleApi from "@/apis/roles";
import permissionApi from "@/apis/permissions";
import utils from "@/utils";

const { t } = useI18n();

const props = defineProps({
  item: Object,
});

const emit = defineEmits(["close"]);

const loading = ref(false);

const step = ref(1);
const open = ref(false);
const messagesStore = useMessageStore();
const selectedPermissions = ref([]);

const roleId = ref(null);
const role = ref({});

watch(
  () => props.item,
  (val) => {
    if (val) {
      role.value = val;
      roleId.value = val.id;
      selectedPermissions.value = val.permissions.map(
        (permission) => permission.id
      );
      step.value = 1;
      open.value = true;
    }
  },
  { immediate: true }
);

watch(open, (val) => {
  if (!val) {
    role.value = {};
    roleId.value = null;
    step.value = 1;
    selectedPermissions.value = [];
  }
});

const title = computed(() => {
  return roleId.value ? t("roles.form.editTitle") : t("roles.form.addTitle");
});

const isEditing = computed(() => {
  return roleId.value != null;
});

const openForm = () => {
  open.value = true;
};

const closeForm = () => {
  open.value = false;
  loading.value = false;
  emit("close");
};

const submit = async () => {
  loading.value = true;

  if (!isEditing.value) {
    roleApi
      .create({
        name: role.value.name,
        description: role.value.description,
      })
      .then((rs) => {
        messagesStore.add({
          text: t("common.addSuccess", { name: "Role" }),
          color: "success",
        });

        closeForm();
      })
      .catch((err) => {
        messagesStore.add({
          text: err.response?.data.msg,
          color: "error",
        });
      });
  } else {
    roleApi
      .updateById(role.value.id, role.value)
      .then((rs) => {
        messagesStore.add({
          text: t("common.updateSuccess", { name: "Role" }),
          color: "success",
        });

        closeForm();
      })
      .catch((err) => {
        messagesStore.add({ text: t("errors.common"), color: "error" });
      });
  }
};

const addRoleAndNextStep = async () => {
  if (!isEditing.value) {
    roleApi
      .create({
        name: role.value.name,
        description: role.value.description,
      })
      .then((rs) => {
        messagesStore.add({
          text: t("common.addSuccess", { name: "Role" }),
          color: "success",
        });

        roleId.value = rs.id;
        step.value = 2;
      })
      .catch((err) => {
        messagesStore.add({
          text: err.response?.data.msg,
          color: "error",
        });
      });
  } else {
    roleApi
      .updateById(role.value.id, role.value)
      .then((rs) => {
        messagesStore.add({
          text: t("common.updateSuccess", { name: "Role" }),
          color: "success",
        });

        roleId.value = rs.id;
        step.value = 2;
      })
      .catch((err) => {
        messagesStore.add({ text: t("errors.common"), color: "error" });
      });
  }
};

const assignPermissionsToRole = () => {
  roleApi
    .managePermissions(roleId.value, selectedPermissions.value)
    .then((rs) => {
      messagesStore.add({
        text: t("roles.form.assignedPermissionsSuccess"),
        color: "success",
      });

      closeForm();
    })
    .catch((err) => {
      messagesStore.add({
        text: err.response?.data.msg,
        color: "error",
      });
    });
};
</script>
