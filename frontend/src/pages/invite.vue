<route lang="yaml">
meta:
  layout: auth
  breadcrumb: auth.invite.title
</route>

<template>
  <Card>
    <CardHeader class="pb-4">
      <CardTitle class="text-lg">{{ $t('auth.invite.title') }}</CardTitle>
      <CardDescription v-if="state === 'new-user'">
        {{ $t('auth.invite.description') }}
      </CardDescription>
    </CardHeader>
    <CardContent>
      <!-- Invalid / expired token -->
      <div v-if="state === 'invalid'" class="text-center py-4 space-y-2">
        <p class="text-sm text-destructive">{{ $t('auth.invite.invalidLink') }}</p>
        <p class="text-sm text-muted-foreground">{{ $t('auth.invite.contactAdmin') }}</p>
      </div>

      <!-- Loading preflight -->
      <div v-else-if="state === 'loading'" class="py-4 space-y-3">
        <Skeleton class="h-10 w-full" />
        <Skeleton class="h-10 w-full" />
        <Skeleton class="h-10 w-full" />
      </div>

      <!-- Logged in as wrong account -->
      <div v-else-if="state === 'wrong-account'" class="text-center py-4 space-y-3">
        <p class="text-sm text-muted-foreground">{{ $t('auth.invite.wrongAccount', { email: currentUserEmail }) }}</p>
        <p class="text-sm text-muted-foreground">{{ $t('auth.invite.logoutFirst') }}</p>
        <Button class="w-full" @click="onLogout" :disabled="isLoading">
          <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
          {{ $t('auth.invite.logout') }}
        </Button>
      </div>

      <!-- Existing user - accept with one click -->
      <div v-else-if="state === 'existing-user'" class="space-y-4">
        <p v-if="errorMessage" class="text-sm text-destructive">{{ errorMessage }}</p>
        <Button class="w-full" @click="onAcceptExisting" :disabled="isLoading">
          <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
          {{ $t('auth.invite.acceptAs', { email: inviteEmail }) }}
        </Button>
      </div>

      <!-- New user - name + password form -->
      <form v-else-if="state === 'new-user'" @submit.prevent="onSubmitNew" class="space-y-4">
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { useOrganizationStore } from '@/stores/organization'
import { useSubscriptionStore } from '@/stores/subscription'
import { useErrorHandler } from '@/composables/useErrorHandler'

type InviteState = 'loading' | 'invalid' | 'wrong-account' | 'existing-user' | 'new-user'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const profileStore = useProfileStore()
const organizationStore = useOrganizationStore()
const subscriptionStore = useSubscriptionStore()
const { resolveError } = useErrorHandler()

const inviteToken = (route.query.token as string) || ''

const state = ref<InviteState>(inviteToken ? 'loading' : 'invalid')
const inviteEmail = ref('')
const form = reactive({ name: '', password: '' })
const errors = reactive({ name: '', password: '' })
const isLoading = ref(false)
const errorMessage = ref('')

const currentUserEmail = computed(() => profileStore.user?.email ?? '')

onMounted(async () => {
  if (!inviteToken) return

  // Remove the token from the URL without triggering a Vue Router navigation.
  window.history.replaceState(null, '', route.path)

  try {
    const { data } = await authApi.inviteStatus(inviteToken)
    inviteEmail.value = data.email

    if (authStore.isAuthenticated && currentUserEmail.value !== data.email) {
      state.value = 'wrong-account'
      return
    }

    if (!data.user_exists) {
      state.value = 'new-user'
      return
    }

    state.value = 'existing-user'
  } catch {
    state.value = 'invalid'
  }
})

async function _finishAccept(inviteTokenValue: string, name?: string, password?: string) {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const { data: token } = await authApi.completeInvite({
      invite_token: inviteTokenValue,
      ...(name !== undefined && { name }),
      ...(password !== undefined && { password }),
    })
    authStore.setSession(token)
    await Promise.all([
      profileStore.fetchMe(),
      organizationStore.fetchOrganizations(),
      subscriptionStore.fetchSubscriptionStatus(),
    ])
    router.push('/')
  } catch (err: unknown) {
    errorMessage.value = resolveError(err)
  } finally {
    isLoading.value = false
  }
}

async function onAcceptExisting() {
  await _finishAccept(inviteToken)
}

function validate() {
  errors.name = form.name.trim() ? '' : t('common.nameRequired')
  errors.password = form.password.length >= 8 ? '' : t('common.passwordMinLength')
  return !errors.name && !errors.password
}

async function onSubmitNew() {
  if (!validate()) return
  await _finishAccept(inviteToken, form.name, form.password)
}

async function onLogout() {
  isLoading.value = true
  try {
    await authStore.logout()
    // Full reload so onMounted re-runs with the token after the component remounts.
    window.location.href = `${route.path}?token=${encodeURIComponent(inviteToken)}`
  } finally {
    isLoading.value = false
  }
}
</script>
