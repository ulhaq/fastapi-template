<template>
  <header class="h-14 border-b border-border bg-background flex items-center px-4 gap-4 shrink-0">
    <!-- Mobile menu button -->
    <button
      @click="uiStore.toggleSidebar()"
      class="lg:hidden p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
    >
      <Menu class="w-5 h-5" />
    </button>

    <!-- Breadcrumb -->
    <div class="flex items-center gap-1.5 text-sm flex-1">
      <span class="text-muted-foreground">{{ $t('nav.pages') }}</span>
      <ChevronRight class="w-3.5 h-3.5 text-muted-foreground/50" />
      <span class="font-medium text-foreground">{{ breadcrumb }}</span>
    </div>

    <!-- Right side -->
    <div class="flex items-center gap-2">
      <!-- Dark mode toggle -->
      <button
        @click="toggleDark()"
        class="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
      >
        <Sun v-if="isDark" class="w-4 h-4" />
        <Moon v-else class="w-4 h-4" />
      </button>

      <!-- Language toggle -->
      <button
        @click="toggleLocale()"
        class="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors text-xs font-medium"
      >
        {{ locale.toUpperCase() }}
      </button>

      <!-- User menu -->
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <button class="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-accent transition-colors">
            <div class="w-7 h-7 rounded-full bg-primary flex items-center justify-center">
              <span class="text-primary-foreground text-xs font-semibold">{{ userInitials }}</span>
            </div>
            <ChevronDown class="w-3.5 h-3.5 text-muted-foreground" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" class="w-52">
          <DropdownMenuLabel>
            <p class="font-medium">{{ user?.name }}</p>
            <p class="text-xs text-muted-foreground font-normal">{{ user?.email }}</p>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem as-child>
            <RouterLink to="/settings" class="cursor-pointer flex items-center">
              <Settings class="w-4 h-4 mr-2" />
              {{ $t('nav.settings') }}
            </RouterLink>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem @click="handleLogout" class="text-destructive cursor-pointer focus:text-destructive">
            <LogOut class="w-4 h-4 mr-2" />
            {{ $t('nav.logOut') }}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Menu, ChevronRight, ChevronDown, Sun, Moon, Settings, LogOut } from 'lucide-vue-next'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const authStore = useAuthStore()
const uiStore = useUiStore()
const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const isDark = ref(document.documentElement.classList.contains('dark'))

function toggleDark() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
}

function toggleLocale() {
  locale.value = locale.value === 'en' ? 'da' : 'en'
  localStorage.setItem('locale', locale.value)
}

const user = computed(() => authStore.user)
const breadcrumb = computed(() => {
  const key = route.meta.breadcrumb as string | undefined
  return key ? t(key) : ''
})

const userInitials = computed(() => {
  if (!user.value?.name) return '?'
  return user.value.name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
})

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
