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
        <v-form ref="roleForm" @submit.prevent="submit">
          <v-card>
            <v-card-title>
              <span class="text-h6">{{ title }}</span>
            </v-card-title>

            <v-card-text>
              <v-row>
                <v-col>
                  <v-text-field
                    :label="t('common.name')"
                    v-model="roleStore.role.name"
                    :rules="[validation.required, validation.minLength(1)]"
                  ></v-text-field>
                </v-col>
              </v-row>
              <v-row>
                <v-col>
                  <v-text-field
                    :label="t('common.description')"
                    v-model="roleStore.role.description"
                    :rules="[validation.required]"
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
                :loading="roleStore.loading"
                @click="addRoleAndNextStep"
              ></v-btn>
              <v-btn
                color="white"
                :text="t('common.save')"
                size="large"
                variant="elevated"
                type="submit"
                :loading="roleStore.loading"
              ></v-btn>
            </v-card-actions>
          </v-card>
        </v-form>
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
import { useRoleStore } from "@/stores/role";
import { validation } from "@/plugins/validation";

const { t } = useI18n();

const roleStore = useRoleStore();

const roleForm = ref(null);

const step = ref(1);
const open = ref(false);
const selectedPermissions = ref([]);

const roleId = ref(null);

watch(
  () => roleStore.role,
  (val) => {
    if (val.id) {
      roleStore.setRole(val);
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
    roleStore.resetRole();
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
  roleStore.loading = false;
};

const submit = async () => {
  const { valid } = await roleForm.value.validate();
  if (!valid) return;

  try {
    if (!isEditing.value) {
      await roleStore.createRole(roleStore.role);
    } else {
      await roleStore.updateRole(roleStore.role);
    }

    closeForm();
  } catch (err) {
    console.error("Error during submit:", err);
  }
};

const addRoleAndNextStep = async () => {
  const { valid } = await roleForm.value.validate();
  if (!valid) return;

  try {
    let rs;

    if (!isEditing.value) {
      rs = await roleStore.createRole(roleStore.role);
    } else {
      rs = await roleStore.updateRole(roleStore.role);
    }

    roleId.value = rs.id;
    step.value = 2;
  } catch (err) {
    console.error("Error during addRoleAndNextStep:", err);
  }
};

const assignPermissionsToRole = async () => {
  try {
    await roleStore.managePermissions(roleId.value, selectedPermissions.value);

    closeForm();
  } catch (err) {
    console.error("Error during assignPermissionsToRole:", err);
  }
};
</script>
