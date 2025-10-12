<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card v-if="!newPassword" class="pa-6" elevation="8" width="450">
      <v-card-title class="text-h5 text-center mb-6">{{
        t("reset.form.requestTitle")
      }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" class="pb-4" @submit.prevent="request">
          <v-text-field
            v-model="email"
            :label="t('common.email')"
            :rules="[validation.required, validation.email]"
            type="email"
          />
          <v-btn block class="mb-4" color="primary" type="submit">
            {{ t("reset.form.submit") }}
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
        <v-form v-model="valid" class="pb-4" @submit.prevent="reset">
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
          <v-btn block class="mb-4" color="primary" type="submit">
            {{ t("reset.form.submit") }}
          </v-btn>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
  import { computed, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRoute } from 'vue-router'
  import authApi from '@/apis/auth'
  import { validation } from '@/plugins/validation'
  import { useAuthStore } from '@/stores/auth'
  import { useMessageStore } from '@/stores/message'

  const route = useRoute()
  const authStore = useAuthStore()
  const messageStore = useMessageStore()

  const { t } = useI18n()

  const email = ref('')
  const password = ref('')
  const valid = ref(false)

  const newPassword = computed(() => {
    return route.params.token
  })

  function request () {
    authApi.requestPasswordReset(email.value)
  }

  async function reset () {
    try {
      await authApi.resetPassword(password.value, route.params.token)

      authStore.login(email.value, password.value)
    } catch (error) {
      let msg
      if (error?.response?.data?.msg) {
        msg = error.response.data.msg
      } else if (error?.response?.data?.detail?.[0]) {
        const loc = error.response.data.detail[0].loc
        const locPart = Array.isArray(loc) ? loc.at(-1) : ''
        const detailMsg = error.response.data.detail[0].msg || ''
        msg = `${locPart} ${detailMsg}`.toLowerCase()
      } else {
        msg = error.response.data.msg
      }
      messageStore.add({ text: msg, color: 'error' })
    }
  }

  onMounted(async () => {
  //
  })
</script>
