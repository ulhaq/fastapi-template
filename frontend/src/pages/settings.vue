<route lang="yaml">
meta:
  layout: dashboard
  requiresAuth: true
  breadcrumb: nav.settings
</route>

<template>
  <div class="flex gap-8 animate-fade-in">
    <!-- Settings sub-nav -->
    <nav class="w-44 shrink-0 space-y-0.5">
      <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 pb-1.5">
        {{ $t('settings.account') }}
      </p>
      <RouterLink
        v-for="item in accountItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors"
        :class="isActive(item.to, item.exact)
          ? 'bg-accent text-accent-foreground font-medium'
          : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'"
      >
        <component :is="item.icon" class="w-4 h-4 shrink-0" />
        {{ item.label }}
      </RouterLink>

      <div class="pt-4 space-y-0.5">
        <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 pb-1.5">
          {{ $t('settings.workspace') }}
        </p>
        <RouterLink
          v-for="item in workspaceItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors"
          :class="isActive(item.to)
            ? 'bg-accent text-accent-foreground font-medium'
            : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'"
        >
          <component :is="item.icon" class="w-4 h-4 shrink-0" />
          {{ item.label }}
        </RouterLink>
      </div>

      <div class="pt-4 space-y-0.5">
        <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 pb-1.5">
          {{ $t('settings.administration') }}
        </p>
        <RouterLink
          v-for="item in adminItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors"
          :class="isActive(item.to)
            ? 'bg-accent text-accent-foreground font-medium'
            : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'"
        >
          <component :is="item.icon" class="w-4 h-4 shrink-0" />
          {{ item.label }}
        </RouterLink>
      </div>
    </nav>

    <!-- Page content -->
    <div class="flex-1 min-w-0">
      <RouterView />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { User, Lock, Users, Shield, Building2, Receipt } from 'lucide-vue-next'
import { usePermission } from '@/composables/usePermission'

const route = useRoute()
const { t } = useI18n()
const { hasPermission } = usePermission()

const accountItems = computed(() => [
  { to: '/settings', label: t('settings.profile'), icon: User, exact: true },
  { to: '/settings/security', label: t('settings.security'), icon: Lock },
])

const workspaceItems = computed(() => [
  { to: '/settings/users', label: t('nav.users'), icon: Users },
  { to: '/settings/roles', label: t('nav.roles'), icon: Shield },
  ...(hasPermission('read:subscription') ? [{ to: '/settings/billing', label: t('nav.billing'), icon: Receipt }] : []),
])

const adminItems = computed(() => [
  { to: '/settings/organizations', label: t('nav.organizations'), icon: Building2 },
])

function isActive(path: string, exact = false): boolean {
  if (exact) return route.path === path
  return route.path.startsWith(path)
}
</script>
