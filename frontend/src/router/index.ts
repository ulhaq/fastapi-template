import { createRouter, createWebHistory } from 'vue-router'
import { routes } from 'vue-router/auto-routes'
import type { RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'

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

  const profileStore = useProfileStore()

  if (to.meta.permission && !profileStore.hasPermission(to.meta.permission)) {
    return { path: '/' }
  }

  // Require active subscription before accessing the app.
  // Allow billing-related routes so the user can complete checkout.
  // Only redirect to billing if the user has permission to view it — otherwise
  // they would loop between '/' and '/settings/billing' indefinitely.
  const billingPaths = ['/settings/billing', '/billing/success', '/billing/cancel']
  const isBillingRoute = billingPaths.some((p) => to.path.startsWith(p))
  if (
    authStore.isAuthenticated
    && !authStore.hasActiveSubscription
    && to.meta.requiresAuth
    && !isBillingRoute
    && profileStore.hasPermission('read:subscription')
  ) {
    return { path: '/settings/billing' }
  }

})

export { router }
