<template>
  <v-slide-x-reverse-transition>
    <v-btn
      v-if="messageStore.queue.length > 0 && !isMessagePanelExpanded"
      color="white"
      density="comfortable"
      elevation="24"
      icon="mdi-bell"
      location="top right"
      position="fixed"
      size="small"
      style="z-index:9999"
      :title="t('messagePanel.show')"
      @click="toggleMessagePanel"
    />
    <v-card
      v-if="messageStore.queue.length > 0 && isMessagePanelExpanded"
      class="d-flex flex-column"
      elevation="24"
      location="top right"
      max-height="75%"
      min-width="25%"
      position="fixed"
      rounded
      :style="{zIndex: 9999}"
    >
      <v-card-title v-if="authStore.isAuthenticated" class="d-flex">
        {{ t('messagePanel.title') }}
        <v-spacer />
        <v-btn
          density="comfortable"
          elevation="0"
          icon="mdi-arrow-right"
          :title="t('messagePanel.hide')"
          @click="toggleMessagePanel"
        />
      </v-card-title>

      <v-card-text
        class="pa-0"
        style="overflow-y: auto"
      >
        <v-slide-x-reverse-transition group>
          <message v-for="msg in messageStore.queue" :key="`${msg.time}-${msg.text}`" :class="{'mb-2':messageStore.queue.length>1}" :message="msg" />
        </v-slide-x-reverse-transition>
      </v-card-text>

      <v-card-actions v-if="messageStore.queue.length>1" class="d-flex justify-center pa-0 ma-0" style="min-height:0">
        <v-btn
          block
          class="pa-0"
          rounded="0"
          :text="t('common.clearAll')"
          :title="t('common.clearAll')"
          @click="messageStore.clear"
        />
      </v-card-actions>
    </v-card>
  </v-slide-x-reverse-transition>
</template>

<script setup>
  import { ref, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useAuthStore } from '@/stores/auth'
  import { useMessageStore } from '@/stores/message'

  const { t } = useI18n()

  const authStore = useAuthStore()
  const messageStore = useMessageStore()

  const isMessagePanelExpanded = ref(true)

  watch(
    () => messageStore.queue,
    queue => {
      isMessagePanelExpanded.value = queue.length > 0
    },
  )
  function toggleMessagePanel () {
    isMessagePanelExpanded.value = !isMessagePanelExpanded.value
  }

</script>
