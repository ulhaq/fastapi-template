<template>
  <v-overlay
    v-model="modelValue"
    class="align-center justify-center"
    contained
    persistent
  >
    <v-progress-circular
      color="primary"
      indeterminate
      size="64"
    />
  </v-overlay>
</template>

<script setup>
  const modelValue = defineModel()
</script>
