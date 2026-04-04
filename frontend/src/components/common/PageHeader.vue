<template>
  <div class="flex items-start justify-between mb-6">
    <div>
      <h1 class="text-xl font-semibold text-foreground">{{ title }}</h1>
      <p v-if="description" class="text-sm text-muted-foreground mt-0.5">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="flex items-center gap-2 ml-4">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>
