<template>
  <v-container>
    <v-row>
      <v-col class="text-h4">{{ t("settings.title") }}</v-col>
    </v-row>

    <v-row>
      <v-col>
        <v-tabs v-model="tab" class="shrink-0 mb-2">
          <v-tab
            v-for="item in tabs"
            :key="item.name"
            :prepend-icon="item.icon"
            replace
            :text="item.text"
            :to="{ name: 'settings', params: { tab: item.name } }"
            :value="item.name"
          />
        </v-tabs>

        <v-tabs-window v-model="tab">
          <v-tabs-window-item value="profile">
            <v-card flat>
              <v-card-text>
                <profile-form />
              </v-card-text>
            </v-card>
          </v-tabs-window-item>

          <v-tabs-window-item value="security">
            <v-card flat>
              <v-card-text>
                <new-password-form />
              </v-card-text>
            </v-card>
          </v-tabs-window-item>
        </v-tabs-window>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
  import { computed, ref, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRoute } from 'vue-router'

  const { t } = useI18n()
  const route = useRoute()

  const tabs = computed(() => [
    { text: t('settings.tab1.name'), name: 'profile', icon: 'mdi-account' },
    { text: t('settings.tab2.name'), name: 'security', icon: 'mdi-lock' },
  ])

  const tab = ref(route.params.tab || tabs.value[0].name)

  watch(
    () => route.params.tab,
    newVal => {
      tab.value = newVal || tabs.value[0].name
    },
  )
</script>
