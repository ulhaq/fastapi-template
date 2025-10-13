<template>
  <v-btn color="white" size="large" variant="elevated" @click="openForm">
    {{ t("roles.add") }}
  </v-btn>
  <v-dialog v-model="open" max-width="768" persistent>
    <v-stepper
      v-model="step"
      :editable="isEditing"
      hide-actions
      :items="[t('roles.title'), t('permissions.title')]"
    >
      <template #item.1>
        <v-form ref="roleForm" @submit.prevent="submit">
          <v-card>
            <v-card-title>
              <span class="text-h6">{{ title }}</span>
            </v-card-title>

            <v-card-text>
              <v-row>
                <v-col>
                  <v-text-field
                    v-model="roleStore.role.name"
                    :label="t('common.name')"
                    :rules="[validation.required, validation.minLength(1)]"
                  />
                </v-col>
              </v-row>
              <v-row>
                <v-col>
                  <v-text-field
                    v-model="roleStore.role.description"
                    :label="t('common.description')"
                    :rules="[validation.required]"
                  />
                </v-col>
              </v-row>
            </v-card-text>

            <v-card-actions>
              <v-btn
                color="error"
                size="large"
                :text="t('common.cancel')"
                variant="plain"
                @click="closeForm"
              />
              <v-spacer />
              <v-btn
                color="white"
                :loading="roleStore.loading"
                size="large"
                :text="t('roles.form.saveAndNext')"
                variant="elevated"
                @click="addRoleAndNextStep"
              />
              <v-btn
                color="white"
                :loading="roleStore.loading"
                size="large"
                :text="t('common.save')"
                type="submit"
                variant="elevated"
              />
            </v-card-actions>
          </v-card>
        </v-form>
      </template>
      <template #item.2>
        <v-card>
          <v-card-title>
            <span class="text-h6">{{
              t("roles.form.assignPermissionsToRole")
            }}</span>
          </v-card-title>

          <v-card-text>
            <permission-table
              v-model="selectedPermissions"
              :headers="permissionHeaders"
              :toolbar-spacer="false"
            >
              <template #toolbar.action />
            </permission-table>
          </v-card-text>

          <v-card-actions>
            <v-btn
              color="error"
              size="large"
              :text="t('common.cancel')"
              variant="plain"
              @click="closeForm"
            />
            <v-spacer />
            <v-btn
              color="white"
              size="large"
              :text="t('roles.form.assignPermissionsToRole')"
              variant="elevated"
              @click="assignPermissionsToRole"
            />
          </v-card-actions>
        </v-card>
      </template>
    </v-stepper>
  </v-dialog>
</template>

<script setup>
  import { computed, ref, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { validation } from '@/plugins/validation'
  import { useRoleStore } from '@/stores/role'

  const { t } = useI18n()

  const roleStore = useRoleStore()

  const permissionHeaders = computed(() => [
    { title: t('common.name'), key: 'name' },
    { title: t('common.description'), key: 'description' },
  ])

  const roleForm = ref(null)

  const step = ref(1)
  const open = ref(false)
  const selectedPermissions = ref([])

  const roleId = ref(null)

  watch(
    () => roleStore.role,
    val => {
      if (val.id && !open.value) {
        roleStore.setRole({ ...val })
        roleId.value = val.id
        selectedPermissions.value = val.permissions.map(
          permission => permission.id,
        )
        step.value = 1
        open.value = true
      }
    },
    { immediate: true },
  )

  watch(open, val => {
    if (!val) {
      roleStore.resetRole()
      roleId.value = null
      step.value = 1
      selectedPermissions.value = []
    }
  })

  const title = computed(() => {
    return roleId.value ? t('roles.form.editTitle') : t('roles.form.addTitle')
  })

  const isEditing = computed(() => {
    return roleId.value != null
  })

  function openForm () {
    open.value = true
  }

  function closeForm () {
    open.value = false
    roleStore.loading = false
  }

  async function submit () {
    const { valid } = await roleForm.value.validate()
    if (!valid) return

    try {
      await (isEditing.value
        ? roleStore.updateRole(roleStore.role)
        : roleStore.createRole(roleStore.role))

      closeForm()
    } catch (error) {
      console.error('Error during submit:', error)
    }
  }

  async function addRoleAndNextStep () {
    const { valid } = await roleForm.value.validate()
    if (!valid) return

    try {
      const rs = await (isEditing.value
        ? roleStore.updateRole(roleStore.role)
        : roleStore.createRole(roleStore.role))

      roleId.value = rs.id
      step.value = 2
    } catch (error) {
      console.error('Error during addRoleAndNextStep:', error)
    }
  }

  async function assignPermissionsToRole () {
    try {
      await roleStore.managePermissions(roleId.value, selectedPermissions.value)

      closeForm()
    } catch (error) {
      console.error('Error during assignPermissionsToRole:', error)
    }
  }
</script>
