<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card v-if="!token" class="pa-6" elevation="8">
      <v-card-title class="text-h5 text-center mb-6">{{
        t('reset.form.requestTitle')
      }}</v-card-title>
      <v-card-text>
        <v-form ref="requestForm" class="pb-4" @submit.prevent="request">
          <v-text-field
            v-model="email"
            :label="t('common.email')"
            :rules="[rules.required(), rules.email()]"
            type="email"
          />
          <v-btn block class="mb-4" color="primary" type="submit">
            {{ t('common.submit') }}
          </v-btn>
          <v-card-actions>
            <v-btn class="mt-4" :to="{ name: 'register' }">{{
              t('reset.form.newAccount')
            }}</v-btn>
            <v-spacer />
            <v-btn class="mt-4" :to="{ name: 'login' }">{{
              t('reset.form.login')
            }}</v-btn>
          </v-card-actions>
        </v-form>
      </v-card-text>
    </v-card>
    <v-card v-else class="pa-6" elevation="8">
      <v-card-title class="text-h5 text-center mb-6">{{
        t('reset.form.resetTitle')
      }}</v-card-title>
      <v-card-text>
        <v-form ref="resetForm" class="pb-4" @submit.prevent="reset">
          <v-text-field
            v-model="newPassword"
            :label="t('reset.form.newPassword')"
            :rules="[rules.required(), rules.minLength(6)]"
            type="password"
          />
          <v-text-field
            v-model="confirmPassword"
            :label="t('reset.form.confirmPassword')"
            :rules="[
              rules.required(),
              rules.minLength(6),
              rules.matchesField(newPassword, '', t('rules.confirmPassword')),
            ]"
            type="password"
          />
          <v-btn block class="mb-4" color="primary" type="submit">
            {{ t('reset.form.update') }}
          </v-btn>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
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
const newPassword = ref('')
const confirmPassword = ref('')
const requestForm = ref(false)
const resetForm = ref(false)

const token = ref(null)

async function request() {
  const { valid } = await requestForm.value.validate()
  if (!valid) return

  await authStore.requestPasswordReset(email.value).then(() => {
    email.value = null

    messageStore.add({
      text: t('reset.form.requestSuccess'),
      type: 'success',
    })
  })
}

async function reset() {
  const { valid } = await resetForm.value.validate()
  if (!valid) return
  messageStore.clearErrors()

  await authStore.resetPassword(newPassword.value, token.value)

  messageStore.add({ text: t('reset.form.resetSuccess'), type: 'success' })

  router.push({ name: 'login' })
}

onMounted(async () => {
  token.value = route.query.token
  router.replace({ name: 'reset-password' })
})
</script>
