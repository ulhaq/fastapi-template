<template>
  <v-app class="bg-blue-grey-lighten-5">
    <div
      class="position-fixed d-flex flex-column "
      :style="{ top: '10px', right: '10px', 'z-index': 9999}"
    >
      <v-alert
        v-for="msg in messageStore.queue"
        :key="msg.text"
        class="pa-4 mb-2"
        closable
        :icon="false"
        :style="{ width: '400px' }"
        :text="msg.text"
        :type="msg.color"
        variant="elevated"
      />
    </div>

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
