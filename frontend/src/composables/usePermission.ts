import { useAuthStore } from '@/stores/auth'

export function usePermission() {
  const authStore = useAuthStore()

  function hasPermission(permission: string): boolean {
    return authStore.hasPermission(permission)
  }

  function hasAnyPermission(...permissions: string[]): boolean {
    return permissions.some((p) => authStore.hasPermission(p))
  }

  return { hasPermission, hasAnyPermission }
}
