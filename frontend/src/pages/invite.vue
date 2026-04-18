<route lang="yaml">
meta:
  layout: auth
  guestOnly: true
  breadcrumb: auth.invite.title
</route>

<template>
  <Card>
    <CardHeader class="pb-4">
      <CardTitle class="text-lg">{{ $t('auth.invite.title') }}</CardTitle>
      <CardDescription v-if="!error">
        {{ $t('auth.invite.description') }}
      </CardDescription>
    </CardHeader>
    <CardContent>
      <!-- Error state -->
      <div v-if="error" class="text-center py-4 space-y-2">
        <p class="text-sm text-destructive">{{ $t('auth.invite.invalidLink') }}</p>
        <p class="text-sm text-muted-foreground">{{ $t('auth.invite.contactAdmin') }}</p>
      </div>

      <!-- Complete profile form -->
      <form v-else @submit.prevent="onSubmit" class="space-y-4">
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

        <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>

        <Button type="submit" class="w-full" :disabled="isLoading">
          <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
          {{ $t('auth.invite.accept') }}
        </Button>
      </form>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { useTenancyStore } from '@/stores/tenancy'
import { useErrorHandler } from '@/composables/useErrorHandler'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const profileStore = useProfileStore()
const tenancyStore = useTenancyStore()
const { resolveError } = useErrorHandler()

const inviteToken = (route.query.token as string) || ''
if (inviteToken) {
  router.replace({ path: route.path })
}

const error = ref(!inviteToken)
const form = reactive({ name: '', password: '' })
const errors = reactive({ name: '', password: '' })
const isLoading = ref(false)
const errorMessage = ref('')

function validate() {
  errors.name = form.name.trim() ? '' : t('common.nameRequired')
  errors.password = form.password.length >= 8 ? '' : t('common.passwordMinLength')
  return !errors.name && !errors.password
}

async function onSubmit() {
  if (!validate()) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    const { data: token } = await authApi.completeInvite({
      invite_token: inviteToken,
      name: form.name,
      password: form.password,
    })
    authStore.setSession(token)
    await Promise.all([profileStore.fetchMe(), tenancyStore.fetchTenants()])
    router.push('/')
  } catch (err: unknown) {
    errorMessage.value = resolveError(err)
  } finally {
    isLoading.value = false
  }
}
</script>
