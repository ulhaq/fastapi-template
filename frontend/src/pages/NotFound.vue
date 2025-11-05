<template>
  <v-container
    class="fill-height d-flex align-center justify-center text-center"
  >
    <v-card class="pa-8" elevation="6" width="500">
      <v-img
        alt="404 error"
        class="mb-6"
        contain
        height="200"
        src="https://cdn.jsdelivr.net/gh/maizzle/404@main/images/404.svg"
      />
      <v-card-title class="text-h4 font-weight-bold mb-2">
        {{ t('error.404Title') }}
      </v-card-title>
      <v-card-text class="text-subtitle-1 mb-6">
        {{ t('error.404Message') }}
      </v-card-text>
      <v-btn color="primary" @click="$router.push('/')">
        {{ t('error.goHome') }}
      </v-btn>
    </v-card>
  </v-container>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>
