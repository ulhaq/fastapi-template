<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card v-if="!newPassword" class="pa-6" elevation="8" width="450">
      <v-card-title class="text-h5 text-center mb-6">{{
        t("reset.form.requestTitle")
      }}</v-card-title>
      <v-card-text>
        <v-form ref="requestForm" class="pb-4" @submit.prevent="request">
          <v-text-field
            v-model="email"
            :label="t('common.email')"
            :rules="[validation.required, validation.email]"
            type="email"
          />
          <v-btn block class="mb-4" color="primary" type="submit">
            {{ t("common.submit") }}
          </v-btn>
          <v-card-actions>
            <v-btn class="mt-4" :to="{ name: 'register' }">{{
              t("reset.form.newAccount")
            }}</v-btn>
            <v-spacer />
            <v-btn class="mt-4" :to="{ name: 'login' }">{{
              t("reset.form.login")
            }}</v-btn>
          </v-card-actions>
        </v-form>
      </v-card-text>
    </v-card>
    <v-card v-else class="pa-6" elevation="8" width="450">
      <v-card-title class="text-h5 text-center mb-6">{{
        t("reset.form.resetTitle")
      }}</v-card-title>
      <v-card-text>
        <v-form ref="resetForm" class="pb-4" @submit.prevent="reset">
          <v-text-field
            v-model="password"
            :label="t('common.password')"
            :rules="[validation.required, validation.minLength(6)]"
            type="password"
          />
          <v-btn block class="mb-4" color="primary" type="submit">
            {{ t("reset.form.update") }}
          </v-btn>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
  import { computed, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRoute, useRouter } from 'vue-router'
  import { useErrorHandler } from '@/composables/errorHandler'
  import { validation } from '@/plugins/validation'
  import { useAuthStore } from '@/stores/auth'
  import { useMessageStore } from '@/stores/message'

  const route = useRoute()
  const router = useRouter()
  const authStore = useAuthStore()
  const messageStore = useMessageStore()

  const { t } = useI18n()

  const email = ref('')
  const password = ref('')
  const requestForm = ref(false)
  const resetForm = ref(false)

  const newPassword = computed(() => {
    return route.params.token
  })

  async function request () {
    const { valid } = await requestForm.value.validate()
    if (!valid) return

    try {
      await authStore.requestPasswordReset(email.value).then(() => {
        email.value = null

        messageStore.add({ text: t('reset.form.requestSuccess'), type: 'success' })
      })
    } catch (error) {
      useErrorHandler(error.response.data)
    }
  }

  async function reset () {
    messageStore.clear()
    const { valid } = await resetForm.value.validate()
    if (!valid) return

    try {
      await authStore.resetPassword(password.value, route.params.token)

      messageStore.add({ text: t('reset.form.resetSuccess'), type: 'success' })

      router.push({ name: 'login' })
    } catch (error) {
      useErrorHandler(error.response.data)
    }
  }

  onMounted(async () => {
  //
  })
</script>
