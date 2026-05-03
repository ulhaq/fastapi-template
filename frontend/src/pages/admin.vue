<route lang="yaml">
meta:
  layout: dashboard
  requiresAuth: true
  requiresSuperAdmin: true
  breadcrumb: nav.admin
</route>

<template>
  <div class="flex gap-8 animate-fade-in">
    <!-- Admin sub-nav -->
    <nav class="w-44 shrink-0 space-y-0.5">
      <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 pb-1.5">
        {{ $t('admin.title') }}
      </p>
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors"
        :class="
          isActive(item.to)
            ? 'bg-accent text-accent-foreground font-medium'
            : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
        "
      >
        <component :is="item.icon" class="w-4 h-4 shrink-0" />
        {{ item.label }}
      </RouterLink>
    </nav>

    <!-- Page content -->
    <div class="flex-1 min-w-0">
      <RouterView />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Building2, Users, ScrollText } from 'lucide-vue-next'

const route = useRoute()
const { t } = useI18n()

const navItems = computed(() => [
  { to: '/admin/organizations', label: t('admin.organizations'), icon: Building2 },
  { to: '/admin/users', label: t('admin.users'), icon: Users },
  { to: '/admin/audit-logs', label: t('admin.auditLogs'), icon: ScrollText },
])

function isActive(path: string): boolean {
  return route.path.startsWith(path)
}
</script>
