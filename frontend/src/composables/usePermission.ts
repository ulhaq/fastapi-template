import { useProfileStore } from '@/stores/profile'

export function usePermission() {
  const profileStore = useProfileStore()

  function hasPermission(permission: string): boolean {
    return profileStore.hasPermission(permission)
  }

  function hasAnyPermission(...permissions: string[]): boolean {
    return permissions.some((p) => profileStore.hasPermission(p))
  }

  return { hasPermission, hasAnyPermission }
}
