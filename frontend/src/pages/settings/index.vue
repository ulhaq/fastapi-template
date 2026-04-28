<route lang="yaml">
meta:
  breadcrumb: settings.profile
</route>

<template>
  <div class="max-w-2xl">
    <PageHeader :title="$t('settings.profileInfo')" :description="$t('settings.profileInfoDescription')" />

    <Card>
      <CardContent class="pt-6">
        <form @submit.prevent="saveProfile" class="space-y-4">
          <div class="space-y-2">
            <Label>{{ $t('common.name') }}</Label>
            <Input v-model="profile.name" :disabled="savingProfile" />
            <p v-if="profileErrors.name" class="text-xs text-destructive">{{ profileErrors.name }}</p>
          </div>
          <div class="space-y-2">
            <Label>{{ $t('common.email') }}</Label>
            <Input v-model="profile.email" type="text" :disabled="savingProfile" />
            <p v-if="profileErrors.email" class="text-xs text-destructive">{{ profileErrors.email }}</p>
          </div>
          <p v-if="profileError" class="text-sm text-destructive">{{ profileError }}</p>
          <div class="flex justify-end">
            <Button type="submit" size="sm" :disabled="savingProfile">
              <Loader2 v-if="savingProfile" class="w-4 h-4 mr-2 animate-spin" />
              {{ $t('common.saveChanges') }}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loader2 } from 'lucide-vue-next'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader.vue'
import { usersApi } from '@/api/users'
import { useProfileStore } from '@/stores/profile'
import { useToast } from '@/composables/useToast'

const profileStore = useProfileStore()
const { toast } = useToast()
const { t } = useI18n()

const profile = reactive({ name: '', email: '' })
const profileErrors = reactive({ name: '', email: '' })
const profileError = ref('')
const savingProfile = ref(false)

onMounted(() => {
  if (profileStore.user) {
    profile.name = profileStore.user.name
    profile.email = profileStore.user.email
  }
})

async function saveProfile() {
  profileErrors.name = profile.name.trim() ? '' : t('common.nameRequired')
  profileErrors.email = profile.email.trim() ? '' : t('common.emailRequired')
  if (profileErrors.name || profileErrors.email) return

  savingProfile.value = true
  profileError.value = ''
  try {
    const { data } = await usersApi.patchMe({ name: profile.name, email: profile.email })
    profileStore.user = data
    toast({ title: t('settings.profileUpdated') })
  } catch {
    profileError.value = t('settings.failedToSaveChanges')
  } finally {
    savingProfile.value = false
  }
}
</script>
