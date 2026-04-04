<template>
  <div class="min-h-screen bg-gradient-to-br from-background via-muted/30 to-background flex items-center justify-center p-4">
    <div class="w-full max-w-md animate-fade-in">
      <div class="mb-8 text-center">
        <div class="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-primary mb-4">
          <span class="text-primary-foreground font-bold text-lg">A</span>
        </div>
        <h1 class="text-2xl font-semibold tracking-tight text-foreground">{{ $t('app.name') }}</h1>
      </div>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
useI18n()
</script>
