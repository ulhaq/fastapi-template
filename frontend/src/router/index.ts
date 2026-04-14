import { createRouter, createWebHistory } from 'vue-router'
import { routes } from 'vue-router/auto-routes'
import type { RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    layout?: 'auth' | 'dashboard'
    requiresAuth?: boolean
    guestOnly?: boolean
    permission?: string
    breadcrumb?: string
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to: RouteLocationNormalized) => {
  const authStore = useAuthStore()

  if (!authStore.isInitialized) {
    await authStore.initialize()
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return { path: '/' }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // Require active subscription before accessing the app.
  // Allow billing-related routes so the user can complete checkout.
  const billingPaths = ['/settings/billing', '/billing/success', '/billing/cancel']
  const isBillingRoute = billingPaths.some((p) => to.path.startsWith(p))
  if (
    authStore.isAuthenticated
    && !authStore.hasActiveSubscription
    && to.meta.requiresAuth
    && !isBillingRoute
  ) {
    return { path: '/settings/billing' }
  }

})

export { router }
