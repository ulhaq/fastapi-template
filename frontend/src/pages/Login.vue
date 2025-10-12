<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-form ref="loginForm" class="pb-4" @submit.prevent="submit">
      <v-card class="pa-6" elevation="8" width="450">
        <v-card-title class="text-h5 text-center mb-6">{{
          t("login.form.title")
        }}</v-card-title>

        <v-card-text>
          <v-row>
            <v-col>
              <v-text-field
                v-model="email"
                :label="t('common.email')"
                :rules="[validation.required, validation.email]"
                type="email"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-text-field
                v-model="password"
                :label="t('common.password')"
                :rules="[validation.required, validation.minLength(6)]"
                type="password"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-btn
                block
                class="mb-4"
                color="primary"
                :loading="authStore.loading"
                type="submit"
              >
                {{ t("login.form.submit") }}
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>

        <v-card-actions>
          <v-btn :to="{ name: 'register' }">{{
            t("login.form.newAccount")
          }}</v-btn>
          <v-spacer />
          <v-btn :to="{ name: 'reset' }">{{
            t("login.form.resetPassword")
          }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-form>
  </v-container>
</template>

<script setup>
  import { ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { validation } from '@/plugins/validation'
  import { useAuthStore } from '@/stores/auth'

  const { t } = useI18n()
  const authStore = useAuthStore()

  const email = ref('')
  const password = ref('')
  const loginForm = ref(null)

  async function submit () {
    const { valid } = await loginForm.value.validate()
    if (!valid) return

    authStore.login(email.value, password.value)
  }

  onMounted(async () => {
  //
  })
</script>
