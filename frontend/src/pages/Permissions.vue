<template>
  <v-container>
    <v-row>
      <v-col class="text-h4">{{ t("permissions.title") }}</v-col>
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
                {{ t("permissions.add") }}
              </v-btn>
            </template>

            <v-card
              :title="t('permissions.addForm.title')"
              class="bg-blue-grey-lighten-5"
              flat
            >
              <v-card-text>
                <v-row>
                  <v-col>
                    <v-text-field
                      :label="t('permissions.addForm.name')"
                      v-model="permission.name"
                      :rules="[(v) => !!v || t('rules.required')]"
                    ></v-text-field>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col>
                    <v-text-field
                      :label="t('permissions.addForm.description')"
                      v-model="permission.description"
                      :rules="[(v) => !!v || t('rules.required')]"
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
                  :text="t('common.save')"
                  size="large"
                  variant="elevated"
                  @click="addPermission"
                ></v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-toolbar>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <permission-table :key="permissionTableKey" :search="search" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref, shallowRef } from "vue";
import { useMessagesStore } from "@/stores/message";
import SearchBar from "@/components/SearchBar.vue";
import PermissionTable from "@/components/PermissionTable.vue";
import permissionApi from "@/apis/permissions";

const { t } = useI18n();

const dialog = shallowRef(false);
const search = ref("");

const permissionTableKey = ref(true);

const loading = ref(false);

const permission = ref({});

const messagesStore = useMessagesStore();

const addPermission = () => {
  loading.value = true;

  permissionApi
    .create({
      name: permission.value.name,
      description: permission.value.description,
    })
    .then(() => {
      messagesStore.add({
        text: t("permissions.added"),
        color: "success",
      });

      permissionTableKey.value = !permissionTableKey.value;
      permission.value = {};
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
</script>
