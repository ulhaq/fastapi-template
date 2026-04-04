<template>
  <div class="flex flex-col h-full">
    <!-- Logo -->
    <div class="flex items-center gap-2 px-4 py-5 border-b border-sidebar-border">
      <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-sidebar-primary shrink-0">
        <span class="text-sidebar-primary-foreground font-bold text-sm">A</span>
      </div>
      <span class="font-semibold text-sidebar-foreground">{{ $t('app.name') }}</span>
    </div>

    <!-- Tenant Switcher -->
    <div class="px-3 py-3 border-b border-sidebar-border" v-if="tenants.length > 1">
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <button
            class="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
          >
            <Building2 class="w-4 h-4 shrink-0 text-sidebar-foreground/60" />
            <span class="flex-1 text-left truncate font-medium">{{ currentTenantName }}</span>
            <ChevronsUpDown class="w-3.5 h-3.5 text-sidebar-foreground/50" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent class="w-52" align="start">
          <DropdownMenuLabel class="text-xs text-muted-foreground">{{ $t('nav.switchTenant') }}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            v-for="tenant in tenants"
            :key="tenant.id"
            @click="handleSwitchTenant(tenant.id)"
            class="cursor-pointer"
          >
            <Check v-if="currentTenantId === tenant.id" class="w-4 h-4 mr-2" />
            <span v-else class="w-4 h-4 mr-2" />
            {{ tenant.name }}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors"
        :class="isActive(item.to)
          ? 'bg-sidebar-accent text-sidebar-accent-foreground'
          : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground'"
      >
        <component :is="item.icon" class="w-4 h-4 shrink-0" />
        {{ item.label }}
      </RouterLink>

    </nav>

    <!-- User -->
    <div class="px-3 py-3 border-t border-sidebar-border">
      <div class="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-sidebar-foreground/70">
        <div class="w-7 h-7 rounded-full bg-sidebar-primary flex items-center justify-center shrink-0">
          <span class="text-sidebar-primary-foreground text-xs font-semibold">
            {{ userInitials }}
          </span>
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-medium text-sidebar-foreground truncate">{{ user?.name }}</p>
          <p class="text-xs text-sidebar-foreground/50 truncate">{{ user?.email }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LayoutDashboard,
  Settings,
  Check,
  ChevronsUpDown,
  Layers,
  Receipt,
} from 'lucide-vue-next'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { usePermission } from '@/composables/usePermission'

const authStore = useAuthStore()
const route = useRoute()
const { toast } = useToast()
const { t } = useI18n()
const { hasPermission } = usePermission()

const user = computed(() => authStore.user)
const tenants = computed(() => authStore.tenants)

const userInitials = computed(() => {
  if (!user.value?.name) return '?'
  return user.value.name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
})

const currentTenantId = computed(() => {
  const token = authStore.accessToken
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1]!))
    return payload.tid as number | null
  } catch {
    return null
  }
})

const currentTenantName = computed(() => {
  const tenant = tenants.value.find((t) => t.id === currentTenantId.value)
  return tenant?.name ?? t('nav.tenant')
})

const navItems = computed(() => [
  { to: '/', label: t('nav.dashboard'), icon: LayoutDashboard },
  // TODO: replace with domain-specific links
  { to: '/example', label: 'Example', icon: Layers },
  { to: '/settings', label: t('nav.settings'), icon: Settings },
])

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

async function handleSwitchTenant(tenantId: number) {
  if (tenantId === currentTenantId.value) return
  try {
    await authStore.switchTenant(tenantId)
    window.location.reload()
  } catch {
    toast({ title: t('nav.failedToSwitchTenant'), variant: 'destructive' })
  }
}
</script>
