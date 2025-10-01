<template>
  <v-text-field
    :label="t('common.search')"
    append-inner-icon="mdi-magnify"
    density="comfortable"
    class="elevation-0"
    variant="solo"
    hide-details
    clearable
  />
</template>

<script setup>
import { useI18n } from "vue-i18n";

const { t } = useI18n();
</script>
