<template>
  <component :is="currentLayout">
    <RouterView />
  </component>
  <Toaster />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { defineAsyncComponent } from 'vue'
import { Toaster } from '@/components/ui/toast'

const AuthLayout = defineAsyncComponent(() => import('@/layouts/AuthLayout.vue'))
const DashboardLayout = defineAsyncComponent(() => import('@/layouts/DashboardLayout.vue'))

const route = useRoute()

const layouts = {
  auth: AuthLayout,
  dashboard: DashboardLayout,
} as const

const currentLayout = computed(() => layouts[route.meta.layout ?? 'auth'])
</script>
