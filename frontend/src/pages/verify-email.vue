<route lang="yaml">
meta:
  layout: auth
  guestOnly: true
  breadcrumb: auth.verifyEmailTitle
</route>

<template>
  <Card>
    <CardHeader class="pb-4">
      <CardTitle class="text-lg">{{ $t('auth.verifyEmailTitle') }}</CardTitle>
      <CardDescription v-if="!setupToken && !error">
        {{ $t('auth.verifyingEmail') }}
      </CardDescription>
      <CardDescription v-else-if="setupToken">
        {{ $t('auth.completeProfileDescription') }}
      </CardDescription>
    </CardHeader>
    <CardContent>
      <!-- Verifying state -->
      <div v-if="verifying" class="flex justify-center py-6">
        <Loader2 class="w-6 h-6 animate-spin text-muted-foreground" />
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="text-center py-4 space-y-2">
        <p class="text-sm text-destructive">{{ $t('auth.invalidVerifyLink') }}</p>
        <RouterLink
          to="/register"
          class="text-sm text-foreground font-medium hover:underline block mt-2"
        >
          {{ $t('auth.registerAgain') }}
        </RouterLink>
      </div>

      <!-- Complete profile form -->
      <form v-else-if="setupToken" class="space-y-4" @submit.prevent="onSubmit">
        <div class="space-y-2">
          <Label for="name">{{ $t('common.name') }}</Label>
          <Input
            id="name"
            v-model="form.name"
            :placeholder="$t('users.form.namePlaceholder')"
            :disabled="isLoading"
            autofocus
          />
          <p v-if="errors.name" class="text-xs text-destructive">{{ errors.name }}</p>
        </div>
        <div class="space-y-2">
          <Label for="password">{{ $t('common.password') }}</Label>
          <Input
            id="password"
            v-model="form.password"
            type="password"
            :placeholder="$t('common.minCharacters')"
            :disabled="isLoading"
          />
          <p v-if="errors.password" class="text-xs text-destructive">{{ errors.password }}</p>
        </div>

        <div
          class="space-y-1 rounded-md p-3 transition-colors"
          :class="
            termsError
              ? 'bg-destructive/5 border border-destructive/30'
              : 'border border-transparent'
          "
        >
          <div class="flex items-start space-x-2">
            <Checkbox
              id="terms-accepted"
              :model-value="termsAccepted"
              :disabled="isLoading"
              class="mt-0.5"
              @update:model-value="onTermsChange"
            />
            <Label for="terms-accepted" class="text-sm font-normal leading-snug cursor-pointer">
              {{ $t('gdpr.consentLabel') }}
            </Label>
          </div>
          <p v-if="termsError" class="text-xs text-destructive pl-6">{{ termsError }}</p>
        </div>

        <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>

        <Button type="submit" class="w-full" :disabled="isLoading">
          <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
          {{ $t('auth.getStarted') }}
        </Button>
      </form>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loader2 } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useValidation } from '@/composables/useValidation'
import { useRules } from '@/composables/useRules'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { resolveError } = useErrorHandler()

const token = (route.query.token as string) || ''
if (token) {
  router.replace({ path: route.path })
}

const verifying = ref(!!token)
const error = ref(false)
const setupToken = ref('')

const { t } = useI18n()
const rules = useRules()
const { form, errors, validate } = useValidation({
  name: rules.required,
  password: rules.password,
})
const termsAccepted = ref(false)
const termsError = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  if (!token) {
    error.value = true
    verifying.value = false
    return
  }
  try {
    const { data } = await authApi.verifyEmail({ token })
    setupToken.value = data.setup_token
  } catch {
    error.value = true
  } finally {
    verifying.value = false
  }
})

function onTermsChange(v: boolean | 'indeterminate') {
  termsAccepted.value = v === true
  termsError.value = ''
}

async function onSubmit() {
  if (!validate()) return
  if (!termsAccepted.value) {
    termsError.value = t('gdpr.consentRequired')
    return
  }
  isLoading.value = true
  errorMessage.value = ''
  try {
    await authStore.completeRegistration(
      setupToken.value,
      form.name,
      form.password,
      termsAccepted.value,
    )
    router.push('/settings/billing')
  } catch (err: unknown) {
    errorMessage.value = resolveError(err)
  } finally {
    isLoading.value = false
  }
}
</script>
