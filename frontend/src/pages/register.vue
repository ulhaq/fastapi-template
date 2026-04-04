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
      <CardDescription>{{ $t('auth.createAccountDescription') }}</CardDescription>
    </CardHeader>
    <CardContent>
      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label for="name">{{ $t('common.name') }}</Label>
          <Input
            id="name"
            v-model="form.name"
            :placeholder="$t('users.form.namePlaceholder')"
            :disabled="isLoading"
          />
          <p v-if="errors.name" class="text-xs text-destructive">{{ errors.name }}</p>
        </div>
        <div class="space-y-2">
          <Label for="email">{{ $t('common.email') }}</Label>
          <Input
            id="email"
            v-model="form.email"
            type="email"
            :placeholder="$t('auth.emailPlaceholder')"
            :disabled="isLoading"
          />
          <p v-if="errors.email" class="text-xs text-destructive">{{ errors.email }}</p>
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

        <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>

        <Button type="submit" class="w-full" :disabled="isLoading">
          <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
          {{ $t('auth.createAccount') }}
        </Button>
      </form>
    </CardContent>
    <CardFooter class="pt-0">
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
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useErrorHandler } from '@/composables/useErrorHandler'

const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()
const { resolveError, resolveFieldErrors } = useErrorHandler()

const form = reactive({ name: '', email: '', password: '' })
const errors = reactive({ name: '', email: '', password: '' })
const isLoading = ref(false)
const errorMessage = ref('')

function validate() {
  errors.name = form.name.trim() ? '' : t('common.nameRequired')
  errors.email = form.email.trim() ? '' : t('common.emailRequired')
  errors.password = form.password.length >= 8 ? '' : t('common.passwordMinLength')
  return !errors.name && !errors.email && !errors.password
}

async function onSubmit() {
  if (!validate()) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    await authApi.register(form.name, form.email, form.password)
    await authStore.login(form.email, form.password)
    router.push('/')
  } catch (err: unknown) {
    const fieldErrors = resolveFieldErrors(err)
    if (fieldErrors['body__email']) {
      errors.email = fieldErrors['body__email']
    } else {
      errorMessage.value = resolveError(err)
    }
  } finally {
    isLoading.value = false
  }
}
</script>
