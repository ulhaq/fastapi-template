<template>
  <v-row>
    <v-col>
      <v-form
        ref="passwordRef"
        class="position-relative"
        @submit.prevent="changePassword"
      >
        <v-card>
          <v-card-title>
            <span class="text-h5">{{
              t('settings.tab2.passwordForm.title')
            }}</span>
          </v-card-title>

          <v-card-text>
            <v-row>
              <v-col>
                <v-text-field
                  v-model="password"
                  :label="t('settings.tab2.passwordForm.currentPassword')"
                  :rules="[rules.required()]"
                  type="password"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <v-text-field
                  v-model="newPassword"
                  :label="t('settings.tab2.passwordForm.newPassword')"
                  :rules="[rules.required(), rules.minLength(6)]"
                  type="password"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <v-text-field
                  v-model="confirmPassword"
                  :label="t('settings.tab2.passwordForm.confirmPassword')"
                  :rules="[
                    rules.required(),
                    rules.minLength(6),
                    rules.matchesField(
                      newPassword,
                      '',
                      t('rules.confirmPassword'),
                    ),
                  ]"
                  type="password"
                />
              </v-col>
            </v-row>
          </v-card-text>

          <v-card-actions>
            <v-spacer />
            <v-btn
              color="primary"
              :text="t('common.save')"
              type="submit"
              variant="elevated"
            />
          </v-card-actions>
        </v-card>
        <loading v-model="passwordLoading" />
      </v-form>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRules } from 'vuetify/labs/rules'
import { useMessageStore } from '@/stores/message'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const rules = useRules()
const messageStore = useMessageStore()
const userStore = useUserStore()

const passwordRef = ref(null)

const passwordLoading = ref(false)

const password = ref(null)
const newPassword = ref(null)
const confirmPassword = ref(null)

async function changePassword() {
  const { valid } = await passwordRef.value.validate()
  if (!valid) return
  messageStore.clearErrors()

  passwordLoading.value = true

  try {
    await userStore.changePassword(
      password.value,
      newPassword.value,
      confirmPassword.value,
    )

    password.value = null
    newPassword.value = null
    confirmPassword.value = null

    messageStore.add({
      text: t('settings.tab2.passwordForm.passwordSuccess'),
      type: 'success',
    })
  } finally {
    passwordLoading.value = false
  }
}
</script>
