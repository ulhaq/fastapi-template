<template>
  <v-app class="bg-blue-grey-lighten-5">
    <v-sheet
      v-if="messageStore.queue.length > 0"
      class="d-flex flex-column"
      color="transparent"
      max-height="300"
      position="fixed"
      rounded
      :style="{
        zIndex: 9999,
        top: '10px',
        right: '10px',
        overflowY: 'auto',
      }"
      width="400"
    >
      <v-alert
        v-for="msg in messageStore.queue"
        :key="msg.text"
        class="pa-4 mb-2 flex-shrink-0"
        closable
        :icon="false"
        :text="msg.text"
        :type="msg.type"
        variant="elevated"
        @click:close="messageStore.remove(msg)"
      />
    </v-sheet>

    <router-view />
  </v-app>
</template>

<script lang="ts" setup>
  import { useMessageStore } from '@/stores/message'

  const messageStore = useMessageStore()

  onMounted(async () => {
  //
  })
</script>
