<route lang="yaml">
meta:
  breadcrumb: settings.security
</route>

<template>
  <div class="max-w-2xl">
    <PageHeader :title="$t('settings.changePassword')" :description="$t('settings.changePasswordDescription')" />

    <Card>
      <CardContent class="pt-6">
        <form @submit.prevent="savePassword" class="space-y-4">
          <div class="space-y-2">
            <Label>{{ $t('settings.currentPassword') }}</Label>
            <Input v-model="pwd.current" type="password" :disabled="savingPwd" />
            <p v-if="pwdErrors.current" class="text-xs text-destructive">{{ pwdErrors.current }}</p>
          </div>
          <div class="space-y-2">
            <Label>{{ $t('settings.newPassword') }}</Label>
            <Input v-model="pwd.new" type="password" :placeholder="$t('common.minCharacters')" :disabled="savingPwd" />
            <p v-if="pwdErrors.new" class="text-xs text-destructive">{{ pwdErrors.new }}</p>
          </div>
          <div class="space-y-2">
            <Label>{{ $t('settings.confirmNewPassword') }}</Label>
            <Input v-model="pwd.confirm" type="password" :disabled="savingPwd" />
            <p v-if="pwdErrors.confirm" class="text-xs text-destructive">{{ pwdErrors.confirm }}</p>
          </div>
          <p v-if="pwdError" class="text-sm text-destructive">{{ pwdError }}</p>
          <div class="flex justify-end">
            <Button type="submit" size="sm" :disabled="savingPwd">
              <Loader2 v-if="savingPwd" class="w-4 h-4 mr-2 animate-spin" />
              {{ $t('auth.updatePassword') }}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader.vue'
import { usersApi } from '@/api/users'
import { useToast } from '@/composables/useToast'

const { toast } = useToast()
const { t } = useI18n()

const pwd = reactive({ current: '', new: '', confirm: '' })
const pwdErrors = reactive({ current: '', new: '', confirm: '' })
const pwdError = ref('')
const savingPwd = ref(false)

async function savePassword() {
  pwdErrors.current = pwd.current ? '' : t('settings.currentPasswordRequired')
  pwdErrors.new = pwd.new.length >= 8 ? '' : t('common.passwordMinLength')
  pwdErrors.confirm = pwd.new === pwd.confirm ? '' : t('common.passwordsDoNotMatch')
  if (pwdErrors.current || pwdErrors.new || pwdErrors.confirm) return

  savingPwd.value = true
  pwdError.value = ''
  try {
    await usersApi.changePassword({
      password: pwd.current,
      new_password: pwd.new,
      confirm_password: pwd.confirm,
    })
    pwd.current = ''
    pwd.new = ''
    pwd.confirm = ''
    toast({ title: t('settings.passwordUpdated') })
  } catch (err: unknown) {
    const e = err as { response?: { data?: { error_code?: string } } }
    if (e?.response?.data?.error_code === 'login_failed') {
      pwdErrors.current = t('settings.incorrectCurrentPassword')
    } else {
      pwdError.value = t('settings.failedToUpdatePassword')
    }
  } finally {
    savingPwd.value = false
  }
}
</script>
