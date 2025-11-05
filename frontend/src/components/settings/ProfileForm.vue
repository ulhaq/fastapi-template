<template>
  <v-row>
    <v-col>
      <v-form ref="profileRef" class="position-relative" @submit.prevent="updateProfile">
        <v-card>
          <v-card-title>
            <span class="text-h5">{{ t('settings.tab1.profileForm.title') }}</span>
          </v-card-title>

          <v-card-text>
            <v-row>
              <v-col>
                <v-text-field
                  v-model="name"
                  :label="t('common.name')"
                  :rules="[rules.required(), rules.minLength(1)]"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <v-text-field
                  v-model="email"
                  :label="t('common.email')"
                  :rules="[rules.required(), rules.email()]"
                />
              </v-col>
            </v-row>
          </v-card-text>

          <v-card-actions>
            <v-spacer />
            <v-btn
              color="primary"
              size="large"
              :text="t('common.save')"
              type="submit"
              variant="elevated"
            />
          </v-card-actions>
        </v-card>
        <loading v-model="profileLoading" />
      </v-form>
    </v-col>
  </v-row>
</template>

<script setup>
  import { ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRules } from 'vuetify/labs/rules'
  import { useErrorHandler } from '@/composables/errorHandler'
  import { useAuthStore } from '@/stores/auth'
  import { useMessageStore } from '@/stores/message'
  import { useUserStore } from '@/stores/user'

  const { t } = useI18n()
  const rules = useRules()
  const authStore = useAuthStore()
  const messageStore = useMessageStore()
  const userStore = useUserStore()

  const profileRef = ref(null)

  const profileLoading = ref(false)

  const name = ref(null)
  const email = ref(null)

  onMounted(() => {
    name.value = authStore.user.name
    email.value = authStore.user.email
  })

  async function updateProfile () {
    const { valid } = await profileRef.value.validate()
    if (!valid) return
    messageStore.clearErrors()

    profileLoading.value = true

    try {
      await userStore.updateProfile(name.value, email.value)

      await authStore.setUser()

      messageStore.add({ text: t('settings.tab1.profileForm.profileSuccess'), type: 'success' })
    } catch (error) {
      useErrorHandler(error)
    } finally {
      profileLoading.value = false
    }
  }
</script>
