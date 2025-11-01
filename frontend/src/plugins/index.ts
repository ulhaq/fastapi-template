/**
 * plugins/index.ts
 *
 * Automatically included in `./src/main.ts`
 */

import type { App } from 'vue'
import { useRoute } from 'vue-router'
import i18n from '@/plugins/i18n'
import validation from '@/plugins/validation'
import vuetify from '@/plugins/vuetify'
import router from '@/router'
import pinia from '@/stores'
import { useAuthStore } from '@/stores/auth'

router.beforeEach(async to => {
  const route = useRoute()
  const authStore = useAuthStore()

  if (authStore.loading && !authStore.isAuthenticated) {
    try {
      await authStore.refreshToken()
    } catch {
      console.log('refresh failed')
    }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    router.replace({ name: 'login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    const redirect = route.query.redirect
    router.replace(redirect?.startsWith('/') ? redirect : { name: 'index' })
  }
})

router.afterEach(to => {
  const defaultTitle = 'My App'
  document.title = to.meta.title || defaultTitle
})

export function registerPlugins (app: App) {
  app.use(router).use(vuetify).use(validation).use(pinia).use(i18n)
}
