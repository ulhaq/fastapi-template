<template>
  <v-text-field
    ref="searchRef"
    v-model="modelValue"
    append-inner-icon="mdi-magnify"
    class="elevation-0"
    clearable
    density="compact"
    hide-details
    persistent-placeholder
    :placeholder="t('common.search')"
    variant="solo"
  />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const searchRef = ref(null)
const modelValue = defineModel()

function handleKeyDown(event) {
  const active = document.activeElement
  const isTyping =
    ['INPUT', 'TEXTAREA'].includes(active.tagName) || active.isContentEditable
  if (isTyping) return

  if (event.key === '/' || (event.ctrlKey && event.key.toLowerCase() === 'k')) {
    event.preventDefault()
    searchRef.value?.$el?.querySelector('input').focus()
  }
}

onMounted(() => window.addEventListener('keydown', handleKeyDown))
onBeforeUnmount(() => window.removeEventListener('keydown', handleKeyDown))
</script>
