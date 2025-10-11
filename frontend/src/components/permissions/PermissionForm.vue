<template>
  <v-btn color="white" size="large" variant="elevated" @click="openForm">
    {{ t("permissions.add") }}
  </v-btn>
  <v-dialog v-model="open" max-width="768" persistent>
    <v-stepper
      :items="[t('permissions.title')]"
      v-model="step"
      hide-actions
      :editable="isEditing"
    >
      <template v-slot:item.1>
        <v-form ref="permissionForm" @submit.prevent="submit">
          <v-card>
            <v-card-title>
              <span class="text-h6">{{ title }}</span>
            </v-card-title>

            <v-card-text>
              <v-row>
                <v-col>
                  <v-text-field
                    :label="t('common.name')"
                    v-model="permissionStore.permission.name"
                    :rules="[validation.required, validation.minLength(1)]"
                  ></v-text-field>
                </v-col>
              </v-row>
              <v-row>
                <v-col>
                  <v-text-field
                    :label="t('common.description')"
                    v-model="permissionStore.permission.description"
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
                :text="t('common.save')"
                size="large"
                variant="elevated"
                type="submit"
                :loading="permissionStore.loading"
              ></v-btn>
            </v-card-actions>
          </v-card>
        </v-form>
      </template>
    </v-stepper>
  </v-dialog>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref, computed, watch } from "vue";
import { usePermissionStore } from "@/stores/permission";
import { validation } from "@/plugins/validation";

const { t } = useI18n();

const permissionStore = usePermissionStore();

const permissionForm = ref(null);

const step = ref(1);
const open = ref(false);

const permissionId = ref(null);

watch(
  () => permissionStore.permission,
  (val) => {
    if (val.id) {
      permissionStore.setPermission(val);
      permissionId.value = val.id;
      step.value = 1;
      open.value = true;
    }
  },
  { immediate: true }
);

watch(open, (val) => {
  if (!val) {
    permissionStore.resetPermission();
    permissionId.value = null;
    step.value = 1;
  }
});

const title = computed(() => {
  return permissionId.value
    ? t("permissions.form.editTitle")
    : t("permissions.form.addTitle");
});

const isEditing = computed(() => {
  return permissionId.value != null;
});

const openForm = () => {
  open.value = true;
};

const closeForm = () => {
  open.value = false;
  permissionStore.loading = false;
};

const submit = async () => {
  const { valid } = await permissionForm.value.validate();
  if (!valid) return;

  try {
    if (!isEditing.value) {
      await permissionStore.createPermission(permissionStore.permission);
    } else {
      await permissionStore.updatePermission(permissionStore.permission);
    }

    closeForm();
  } catch (err) {
    console.error("Error during submit:", err);
  }
};
</script>
