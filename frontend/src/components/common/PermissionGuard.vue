<template>
  <slot v-if="hasPermission(permission)" />
</template>

<script setup lang="ts">
import { usePermission } from '@/composables/usePermission'

defineProps<{ permission: string }>()

const { hasPermission } = usePermission()
</script>
