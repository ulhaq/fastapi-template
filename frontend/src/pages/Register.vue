<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card class="pa-6" elevation="8" width="450">
      <v-card-title class="text-h5 text-center mb-6">{{
        t("register.form.title")
      }}</v-card-title>
      <v-card-text>
        <v-form ref="registerForm" class="pb-4" @submit.prevent="submit">
          <v-text-field
            v-model="name"
            :label="t('common.name')"
            :rules="[validation.required]"
            type="name"
          />
          <v-text-field
            v-model="email"
            :label="t('common.email')"
            :rules="[validation.required, validation.email]"
            type="email"
          />
          <v-text-field
            v-model="password"
            :label="t('common.password')"
            :rules="[validation.required, validation.minLength(6)]"
            type="password"
          />
          <v-btn
            block
            class="mb-4"
            color="primary"
            :loading="authStore.loading"
            type="submit"
          >
            {{ t("register.form.submit") }}
          </v-btn>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-btn :to="{ name: 'login' }">{{
          t("register.form.login")
        }}</v-btn>
        <v-spacer />
        <v-btn :to="{ name: 'reset' }">{{
          t("register.form.resetPassword")
        }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
  import { ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRouter } from 'vue-router'
  import { useErrorHandler } from '@/composables/errorHandler'
  import { validation } from '@/plugins/validation'
  import { useAuthStore } from '@/stores/auth'
  import { useMessageStore } from '@/stores/message'

  const { t } = useI18n()
  const router = useRouter()
  const authStore = useAuthStore()
  const messageStore = useMessageStore()

  const name = ref('')
  const email = ref('')
  const password = ref('')
  const registerForm = ref(null)

  async function submit () {
    messageStore.clear()
    const { valid } = await registerForm.value.validate()
    if (!valid) return

    try {
      await authStore.register(name.value, email.value, password.value)

      await authStore.login(email.value, password.value)

      router.push({ name: 'index' })
    } catch (error) {
      useErrorHandler(error.response.data)
    }
  }

  onMounted(async () => {
  //
  })
</script>
