<route lang="yaml">
meta:
  layout: auth
  guestOnly: true
  breadcrumb: auth.loginTitle
</route>

<template>
  <Card>
    <CardHeader class="pb-4">
      <CardTitle class="text-lg">{{ $t('auth.signIn') }}</CardTitle>
      <CardDescription>{{ $t('auth.signInDescription') }}</CardDescription>
    </CardHeader>
    <CardContent>
      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label for="email">{{ $t('common.email') }}</Label>
          <Input
            id="email"
            v-model="email"
            type="text"
            :placeholder="$t('auth.emailPlaceholder')"
            autocomplete="email"
            :disabled="isLoading"
          />
        </div>
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <Label for="password">{{ $t('common.password') }}</Label>
            <RouterLink
              to="/forgot-password"
              class="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              {{ $t('auth.forgotPassword') }}
            </RouterLink>
          </div>
          <Input
            id="password"
            v-model="password"
            type="password"
            placeholder="••••••••"
            autocomplete="current-password"
            :disabled="isLoading"
          />
        </div>

        <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>

        <Button type="submit" class="w-full" :disabled="isLoading">
          <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
          {{ $t('auth.signIn') }}
        </Button>
      </form>
    </CardContent>
    <CardFooter class="pt-0">
      <p class="text-sm text-muted-foreground text-center w-full">
        {{ $t('auth.dontHaveAccount') }}
        <RouterLink to="/register" class="text-foreground font-medium hover:underline">
          {{ $t('auth.createOne') }}
        </RouterLink>
      </p>
    </CardFooter>
  </Card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth'
import { useErrorHandler } from '@/composables/useErrorHandler'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { resolveError } = useErrorHandler()
const { t } = useI18n()

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

async function onSubmit() {
  if (!email.value || !password.value) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    await authStore.login(email.value, password.value)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: unknown) {
    errorMessage.value = resolveError(err)
  } finally {
    isLoading.value = false
  }
}
</script>
