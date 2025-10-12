/**
 * router/index.ts
 *
 * Automatic routes for `./src/pages/*.vue`
 */

// import { routes } from 'vue-router/auto-routes'
import { setupLayouts } from 'virtual:generated-layouts'
import { createRouter, createWebHistory } from 'vue-router/auto'
import Index from '@/pages/Index.vue'
import Login from '@/pages/Login.vue'
import NotFound from '@/pages/NotFound.vue'
import Permissions from '@/pages/Permissions.vue'
import Register from '@/pages/Register.vue'
import ResetPassword from '@/pages/ResetPassword.vue'
import Roles from '@/pages/Roles.vue'
import Users from '@/pages/Users.vue'

const routes = [
  {
    path: '/:catchAll(.*)',
    name: '404',
    component: NotFound,
    meta: {
      layout: 'empty',
    },
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: {
      title: 'Login',
      layout: 'empty',
      requiresGuest: true,
    },
  },
  {
    path: '/reset/:token?',
    name: 'reset',
    component: ResetPassword,
    meta: {
      title: 'Reset Password',
      layout: 'empty',
      requiresGuest: true,
    },
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
    meta: {
      title: 'Register',
      layout: 'empty',
      requiresGuest: true,
    },
  },
  {
    path: '/',
    name: 'index',
    component: Index,
    meta: {
      title: 'Home',
      requiresAuth: true,
    },
  },
  {
    path: '/users',
    name: 'users',
    component: Users,
    meta: {
      title: 'Users',
      requiresAuth: true,
    },
  },
  {
    path: '/roles',
    name: 'roles',
    component: Roles,
    meta: {
      title: 'Roles',
      requiresAuth: true,
    },
  },
  {
    path: '/permissions',
    name: 'permissions',
    component: Permissions,
    meta: {
      title: 'Permissions',
      requiresAuth: true,
    },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: setupLayouts(routes),
})

// Workaround for https://github.com/vitejs/vite/issues/11804
router.onError((err, to) => {
  if (err?.message?.includes?.('Failed to fetch dynamically imported module')) {
    if (localStorage.getItem('vuetify:dynamic-reload')) {
      console.error('Dynamic import error, reloading page did not fix it', err)
    } else {
      console.log('Reloading page to fix dynamic import error')
      localStorage.setItem('vuetify:dynamic-reload', 'true')
      location.assign(to.fullPath)
    }
  } else {
    console.error(err)
  }
})

router.isReady().then(() => {
  localStorage.removeItem('vuetify:dynamic-reload')
})

export default router
