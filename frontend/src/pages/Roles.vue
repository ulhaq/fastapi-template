<template>
  <v-container>
    <v-row>
      <v-col class="text-h4">{{ t("roles.title") }}</v-col>
    </v-row>
    <v-row>
      <v-col>
        <role-table />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
  import { useI18n } from 'vue-i18n'
  import RoleTable from '@/components/roles/RoleTable.vue'

  const { t } = useI18n()
</script>
