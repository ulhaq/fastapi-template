<template>
  <v-text-field
    v-model="modelValue"
    append-inner-icon="mdi-magnify"
    class="elevation-0"
    clearable
    density="comfortable"
    hide-details
    :label="t('common.search')"
    variant="solo"
  />
</template>

<script setup>
  import { useI18n } from 'vue-i18n'

  const { t } = useI18n()

  const modelValue = defineModel()
</script>
