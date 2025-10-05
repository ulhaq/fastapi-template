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
          <role-form :item="selectedItem" @close="selectedItem = null" />
        </v-toolbar>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <role-table :search="search" @editItem="editRole" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref } from "vue";
import SearchBar from "@/components/SearchBar.vue";
import RoleForm from "@/components/RoleForm.vue";
import RoleTable from "@/components/RoleTable.vue";

const { t } = useI18n();

const search = ref("");

const selectedItem = ref();

const editRole = (item) => {
  selectedItem.value = item;
};
</script>
