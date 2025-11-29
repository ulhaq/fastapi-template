<template>
  <v-btn color="white" variant="elevated" @click="openForm">
    {{ t('permissions.add') }}
  </v-btn>
  <v-dialog v-model="open" max-width="768" persistent>
    <v-stepper
      v-model="step"
      :editable="isEditing"
      hide-actions
      :items="[t('permissions.title')]"
    >
      <template #item.1>
        <v-form ref="permissionForm" @submit.prevent="submit">
          <v-card>
            <v-card-title>
              <span class="text-h6">{{ title }}</span>
            </v-card-title>

            <v-card-text>
              <v-row>
                <v-col>
                  <v-text-field
                    v-model="permissionStore.permission.name"
                    :label="t('common.name')"
                    :rules="[rules.required(), rules.minLength(1)]"
                  />
                </v-col>
              </v-row>
              <v-row>
                <v-col>
                  <v-text-field
                    v-model="permissionStore.permission.description"
                    :label="t('common.description')"
                    :rules="[rules.required()]"
                  />
                </v-col>
              </v-row>
            </v-card-text>

            <v-card-actions>
              <v-spacer />
              <v-btn
                color="error"
                :text="t('common.cancel')"
                variant="plain"
                @click="closeForm"
              />
              <v-btn
                color="white"
                :text="t('common.save')"
                type="submit"
                variant="elevated"
              />
            </v-card-actions>
          </v-card>
        </v-form>
      </template>
    </v-stepper>

    <loading v-model="permissionStore.loading" />
  </v-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRules } from 'vuetify/labs/rules'
import { useMessageStore } from '@/stores/message'
import { usePermissionStore } from '@/stores/permission'

const { t } = useI18n()
const rules = useRules()
const messageStore = useMessageStore()
const permissionStore = usePermissionStore()

const permissionForm = ref(null)

const step = ref(1)
const open = ref(false)

const permissionId = ref(null)

watch(
  () => permissionStore.permission,
  (val) => {
    if (val.id && !open.value) {
      permissionStore.setPermission({ ...val })
      permissionId.value = val.id
      step.value = 1
      open.value = true
    }
  },
  { immediate: true },
)

watch(open, (val) => {
  if (!val) {
    permissionStore.resetPermission()
    permissionId.value = null
    step.value = 1
  }
})

const title = computed(() => {
  return permissionId.value
    ? t('permissions.form.editTitle')
    : t('permissions.form.addTitle')
})

const isEditing = computed(() => {
  return permissionId.value != null
})

function openForm() {
  open.value = true
}

function closeForm() {
  open.value = false
  permissionStore.loading = false
}

async function submit() {
  const { valid } = await permissionForm.value.validate()
  if (!valid) return
  messageStore.clearErrors()

  if (isEditing.value) {
    await permissionStore.updatePermission(permissionStore.permission)

    messageStore.add({
      text: t('permissions.form.updateSuccess'),
      type: 'success',
    })
  } else {
    await permissionStore.createPermission(permissionStore.permission)

    messageStore.add({
      text: t('permissions.form.addSuccess'),
      type: 'success',
    })
  }

  closeForm()
}
</script>
