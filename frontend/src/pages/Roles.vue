<template>
  <v-container>
    <v-row>
      <v-col class="text-h4">{{ t("roles.title") }}</v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-toolbar color="transparent">
          <search-bar v-model="search" />
          <v-spacer />
          <v-dialog v-model="dialog" max-width="768">
            <template v-slot:activator="{ props: activatorProps }">
              <v-btn
                color="white"
                size="large"
                variant="elevated"
                v-bind="activatorProps"
              >
                {{ t("roles.add") }}
              </v-btn>
            </template>

            <v-stepper
              :items="[t('roles.title'), t('permissions.title')]"
              class="bg-blue-grey-lighten-5"
              v-model="step"
              hide-actions
            >
              <template v-slot:item.1>
                <v-card
                  :title="t('roles.addForm.title')"
                  class="bg-blue-grey-lighten-5"
                  flat
                >
                  <v-card-text>
                    <v-row>
                      <v-col>
                        <v-text-field
                          :label="t('roles.addForm.name')"
                          v-model="role.name"
                          required
                        ></v-text-field>
                      </v-col>
                    </v-row>
                    <v-row>
                      <v-col>
                        <v-text-field
                          :label="t('roles.addForm.description')"
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
                      @click="dialog = false"
                    ></v-btn>
                    <v-spacer></v-spacer>
                    <v-btn
                      color="white"
                      :text="t('roles.addForm.saveAndNext')"
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
                      @click="addRole"
                    ></v-btn>
                  </v-card-actions>
                </v-card>
              </template>
              <template v-slot:item.2>
                <v-card
                  :title="t('roles.addForm.assignPermissionsToRole')"
                  class="bg-blue-grey-lighten-5"
                  flat
                >
                  <v-card-text>
                    <v-row>
                      <v-col>
                        <AddPermissionToRoleTable
                          v-model="selectedPermissions"
                        />
                      </v-col>
                    </v-row>
                  </v-card-text>

                  <v-card-actions>
                    <v-btn
                      color="error"
                      :text="t('common.cancel')"
                      size="large"
                      variant="plain"
                      @click="
                        dialog = false;
                        step = 1;
                      "
                    ></v-btn>
                    <v-spacer></v-spacer>
                    <v-btn
                      color="white"
                      :text="t('roles.addForm.assignPermissionsToRole')"
                      size="large"
                      variant="elevated"
                      @click="assignPermissionsToRole"
                    ></v-btn>
                  </v-card-actions>
                </v-card>
              </template>
            </v-stepper>
          </v-dialog>
        </v-toolbar>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <role-table :key="roleTableKey" :search="search" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref, shallowRef } from "vue";
import { useMessageStore } from "@/stores/message";
import SearchBar from "@/components/SearchBar.vue";
import RoleTable from "@/components/RoleTable.vue";
import AddPermissionToRoleTable from "@/components/AddPermissionToRoleTable.vue";
import roleApi from "@/apis/roles";

const { t } = useI18n();

const roleTableKey = ref(true);

const loading = ref(false);
const search = ref("");

const selectedPermissions = ref([]);

const role = ref({});

const roleId = ref(null);

const step = ref(1);
const dialog = shallowRef(false);
const messagesStore = useMessageStore();

const addRole = () => {
  loading.value = true;

  roleApi
    .create({
      name: role.value.name,
      description: role.value.description,
    })
    .then((rs) => {
      messagesStore.add({
        text: t("roles.added"),
        color: "success",
      });

      roleTableKey.value = !roleTableKey.value;
      role.value = {};
      dialog.value = false;
    })
    .catch((err) => {
      messagesStore.add({
        text: err.response?.data.msg,
        color: "error",
      });
    });

  loading.value = false;
};

const addRoleAndNextStep = () => {
  roleApi
    .create({
      name: role.value.name,
      description: role.value.description,
    })
    .then((rs) => {
      messagesStore.add({
        text: t("roles.added"),
        color: "success",
      });

      roleTableKey.value = !roleTableKey.value;
      role.value = {};
      roleId.value = rs.id;
      step.value = 2;
    })
    .catch((err) => {
      messagesStore.add({
        text: err.response?.data.msg,
        color: "error",
      });
    });
};

const assignPermissionsToRole = () => {
  roleApi
    .managePermissions(roleId.value, selectedPermissions.value)
    .then((rs) => {
      messagesStore.add({
        text: t("roles.assignedPermissions"),
        color: "success",
      });

      selectedPermissions.value = [];
      roleId.value = null;
      dialog.value = false;
      step.value = 1;
    })
    .catch((err) => {
      messagesStore.add({
        text: err.response?.data.msg,
        color: "error",
      });
    });
};
</script>
