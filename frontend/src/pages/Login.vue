<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-form ref="loginForm" class="pb-4" @submit.prevent="submit">
      <v-card class="pa-6" elevation="8">
        <v-card-title class="text-h5 text-center mb-6">{{
          t('login.form.title')
        }}</v-card-title>

        <v-card-text>
          <v-row>
            <v-col>
              <v-text-field
                v-model="email"
                :label="t('common.email')"
                :rules="[rules.required(), rules.email()]"
                density="comfortable"
                type="email"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-text-field
                v-model="password"
                :label="t('common.password')"
                :rules="[rules.required(), rules.minLength(6)]"
                density="comfortable"
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
                {{ t('login.form.submit') }}
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>

        <v-card-actions>
          <v-btn :to="{ name: 'register' }">{{
            t('login.form.newAccount')
          }}</v-btn>
          <v-spacer />
          <v-btn :to="{ name: 'reset' }">{{
            t('login.form.resetPassword')
          }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-form>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { useRules } from 'vuetify/labs/rules'
import { useAuthStore } from '@/stores/auth'
import { useMessageStore } from '@/stores/message'

const { t } = useI18n()
const rules = useRules()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const messageStore = useMessageStore()

const email = ref('')
const password = ref('')
const loginForm = ref(null)

async function submit() {
  const { valid } = await loginForm.value.validate()
  if (!valid) return
  messageStore.clearErrors()

  await authStore.login(email.value, password.value)

  const redirect = route.query.redirect
  router.push(redirect?.startsWith('/') ? redirect : { name: 'index' })
}

onMounted(async () => {
  //
})
</script>
