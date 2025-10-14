<template>
  <div>
    <v-navigation-drawer
      v-model="drawer"
      class="bg-blue-grey-lighten-5 border-e-0 ps-4"
      :location="$vuetify.display.mobile ? 'left' : undefined"
    >
      <v-sheet class="bg-blue-grey-lighten-5 pt-4 pb-8 pl-4">
        <v-img
          aspect-ratio="16/9"
          cover
          src="https://cdn.vuetifyjs.com/docs/images/one/logos/vuetify-logo-light.png"
          :width="150"
        />
      </v-sheet>
      <v-list density="compact" :lines="false" nav>
        <v-list-item
          v-for="(item, i) in items"
          :key="i"
          class="pt-2 pb-2"
          :to="{ name: item.name }"
          :value="item"
        >
          <template #prepend>
            <v-icon :icon="item.icon" />
          </template>

          <v-list-item-title>{{ item.text }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar class="bg-blue-grey-lighten-5" :elevation="0">
      <v-app-bar-nav-icon variant="plain" @click.stop="drawer = !drawer" />

      <v-spacer />

      <v-btn
        v-for="lang in availableLocales"
        :key="lang.key"
        @click="changeLocale(lang.key)"
      >
        {{ lang.title }}
      </v-btn>
      <v-menu>
        <template #activator="{ props }">
          <v-btn icon v-bind="props">
            <v-icon size="40">mdi-account-circle</v-icon>
          </v-btn>
        </template>

        <v-list>
          <v-list-item @click="goToProfile">
            <v-list-item-title>Profile</v-list-item-title>
          </v-list-item>
          <v-list-item @click="logout">
            <v-list-item-title>Logout</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
  </div>
</template>
<script setup>
  import { ref, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useLocale } from 'vuetify'
  import { availableLocales } from '@/locales/index'
  import { useAuthStore } from '@/stores/auth'

  const { current } = useLocale()

  const { t } = useI18n()
  const authStore = useAuthStore()

  function changeLocale (locale) {
    current.value = locale
    localStorage.setItem('locale', locale)
  }

  const items = computed(() => [
    { name: 'index', text: t('menuBar.index'), icon: 'mdi-home' },
    { name: 'users', text: t('menuBar.users'), icon: 'mdi-account-group' },
    { name: 'roles', text: t('menuBar.roles'), icon: 'mdi-shield-account' },
    { name: 'permissions', text: t('menuBar.permissions'), icon: 'mdi-shield-star' },
  ])

  const drawer = ref(true)
  const group = ref(null)

  watch(group, () => {
    drawer.value = true
  })

  function logout () {
    authStore.logout()
  }
</script>
