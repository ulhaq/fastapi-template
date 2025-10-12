<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card class="pa-6" elevation="8" width="450">
      <v-card-title class="text-h5 text-center mb-6">{{
        t("register.form.title")
      }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" class="pb-4" @submit.prevent="submit">
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
    </v-card>
  </v-container>
</template>

<script setup>
  import { ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import authApi from '@/apis/auth'
  import { validation } from '@/plugins/validation'
  import { useAuthStore } from '@/stores/auth'
  import { useMessageStore } from '@/stores/message'

  const { t } = useI18n()
  const authStore = useAuthStore()
  const messageStore = useMessageStore()

  const name = ref('')
  const email = ref('')
  const password = ref('')
  const valid = ref(false)

  async function submit () {
    try {
      const res = await authApi.register(name.value, email.value, password.value)

      console.log(res)
      authStore.login(email.value, password.value)
    } catch (error) {
      let msg
      console.log(error)

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
