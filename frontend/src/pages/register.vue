<route lang="yaml">
meta:
  layout: auth
  guestOnly: true
  breadcrumb: auth.registerTitle
</route>

<template>
  <Card>
    <CardHeader class="pb-4">
      <CardTitle class="text-lg">{{ $t('auth.createAccount') }}</CardTitle>
      <CardDescription>{{ $t('auth.verifyEmailDescription') }}</CardDescription>
    </CardHeader>
    <CardContent>
      <div v-if="sent" class="text-center py-4 space-y-2">
        <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
          <MailCheck v-if="awaitingVerification" class="w-5 h-5 text-primary" />
          <CheckCircle2 v-else class="w-5 h-5 text-primary" />
        </div>
        <p class="text-sm text-muted-foreground">{{ responseMessage }}</p>
        <RouterLink to="/login" class="text-sm text-foreground font-medium hover:underline block mt-4">
          {{ $t('auth.backToSignIn') }}
        </RouterLink>
      </div>
      <form v-else @submit.prevent="onSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label for="email">{{ $t('common.email') }}</Label>
          <Input
            id="email"
            v-model="email"
            type="email"
            :placeholder="$t('auth.emailPlaceholder')"
            :disabled="isLoading"
          />
          <p v-if="errors.email" class="text-xs text-destructive">{{ errors.email }}</p>
        </div>

        <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>

        <Button type="submit" class="w-full" :disabled="isLoading">
          <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
          {{ $t('auth.createAccount') }}
        </Button>
      </form>
    </CardContent>
    <CardFooter v-if="!sent" class="pt-0">
      <p class="text-sm text-muted-foreground text-center w-full">
        {{ $t('auth.alreadyHaveAccount') }}
        <RouterLink to="/login" class="text-foreground font-medium hover:underline">
          {{ $t('auth.signIn') }}
        </RouterLink>
      </p>
    </CardFooter>
  </Card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loader2, MailCheck, CheckCircle2 } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { authApi } from '@/api/auth'
import { useErrorHandler } from '@/composables/useErrorHandler'

const { t } = useI18n()
const { resolveError, resolveFieldErrors } = useErrorHandler()

const email = ref('')
const errors = ref({ email: '' })
const isLoading = ref(false)
const errorMessage = ref('')
const sent = ref(false)
const responseMessage = ref('')
const awaitingVerification = ref(false)

async function onSubmit() {
  errors.value.email = email.value.trim() ? '' : t('common.emailRequired')
  if (errors.value.email) return

  isLoading.value = true
  errorMessage.value = ''
  try {
    const { data } = await authApi.register({ email: email.value })
    responseMessage.value = data.message
    awaitingVerification.value = data.message.toLowerCase().includes('verify')
    sent.value = true
  } catch (err: unknown) {
    const fieldErrors = resolveFieldErrors(err)
    if (fieldErrors['body__email']) {
      errors.value.email = fieldErrors['body__email']
    } else {
      errorMessage.value = resolveError(err)
    }
  } finally {
    isLoading.value = false
  }
}
</script>
