<template>
  <v-footer class="d-flex align-center justify-center ga-2 flex-wrap flex-grow-1 py-3" color="surface-light">
    <router-link
      v-for="link in links"
      :key="link.name"
      class="text-body-1 text-decoration-none mx-2 text-grey-darken-1"
      :to="link"
    >
      {{ link.text }}
    </router-link>

    <div class="flex-1-0-100 text-center text-grey-darken-1">
      &copy; {{ new Date().getFullYear() }} — Template
    </div>
  </v-footer>
</template>

<script setup>
  import { useI18n } from 'vue-i18n'

  const { t } = useI18n()

  const links = computed(() => [
    { name: 'index', text: t('menuBar.index') },
  ])
</script>
