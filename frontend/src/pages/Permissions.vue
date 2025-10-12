<template>
  <v-container>
    <v-row>
      <v-col class="text-h4">{{ t("permissions.title") }}</v-col>
    </v-row>
    <v-row>
      <v-col>
        <permission-table />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
  import { useI18n } from 'vue-i18n'
  import PermissionTable from '@/components/permissions/PermissionTable.vue'

  const { t } = useI18n()
</script>
