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
        :class="
          isActive(item.to, item.exact)
            ? 'bg-accent text-accent-foreground font-medium'
            : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
        "
      >
        <component :is="item.icon" class="w-4 h-4 shrink-0" />
        <span class="flex-1">{{ item.label }}</span>
        <LockKeyhole v-if="item.locked" class="w-3 h-3 shrink-0 text-foreground" />
      </RouterLink>

      <div v-if="workspaceItems.length" class="pt-4 space-y-0.5">
        <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 pb-1.5">
          {{ $t('settings.workspace') }}
        </p>
        <RouterLink
          v-for="item in workspaceItems"
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
      </div>

      <div v-if="adminItems.length" class="pt-4 space-y-0.5">
        <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 pb-1.5">
          {{ $t('settings.administration') }}
        </p>
        <RouterLink
          v-for="item in adminItems"
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
      </div>
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
import {
  User,
  Lock,
  Users,
  Shield,
  Building2,
  Receipt,
  Settings2,
  KeyRound,
  LockKeyhole,
} from 'lucide-vue-next'
import { usePermission } from '@/composables/usePermission'
import { usePlanFeature } from '@/composables/usePlanFeature'
import { PlanFeature } from '@/constants'

const route = useRoute()
const { t } = useI18n()
const { hasPermission, isOwner } = usePermission()
const { hasFeature } = usePlanFeature()

const accountItems = computed(() => [
  { to: '/settings', label: t('settings.profile'), icon: User, exact: true },
  { to: '/settings/security', label: t('settings.security'), icon: Lock },
  ...(hasPermission('manage:api_token')
    ? [
        {
          to: '/settings/api',
          label: t('settings.api'),
          icon: KeyRound,
          locked: !hasFeature(PlanFeature.API_ACCESS),
        },
      ]
    : []),
])

const workspaceItems = computed(() => [
  ...(isOwner.value
    ? [{ to: '/settings/general', label: t('settings.general'), icon: Settings2 }]
    : []),
  ...(hasPermission('read:user')
    ? [{ to: '/settings/users', label: t('nav.users'), icon: Users }]
    : []),
  ...(hasPermission('read:role')
    ? [{ to: '/settings/roles', label: t('nav.roles'), icon: Shield }]
    : []),
  ...(hasPermission('manage:subscription')
    ? [{ to: '/settings/billing', label: t('nav.subscription'), icon: Receipt }]
    : []),
])

const adminItems = computed(() => [
  { to: '/settings/organizations', label: t('nav.organizations'), icon: Building2 },
])

function isActive(path: string, exact = false): boolean {
  if (exact) return route.path === path
  return route.path.startsWith(path)
}
</script>
