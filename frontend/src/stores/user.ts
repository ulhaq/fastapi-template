import { defineStore } from 'pinia'
import { ref } from 'vue'
import userApi from '@/apis/users'

export const useUserStore = defineStore('user', () => {
  const loading = ref(false)

  async function updateProfile(name: string, email: string) {
    loading.value = true
    try {
      return await userApi.updateProfile(name, email)
    } finally {
      loading.value = false
    }
  }

  async function changePassword(
    password: string,
    newPassword: string,
    confirmPassword: string,
  ) {
    loading.value = true
    try {
      return await userApi.changePassword(
        password,
        newPassword,
        confirmPassword,
      )
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    updateProfile,
    changePassword,
  }
})
