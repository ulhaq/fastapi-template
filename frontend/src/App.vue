<template>
  <v-app class="bg-blue-grey-lighten-5">
    <v-snackbar-queue
      v-model="messagesStore.queue"
      location="top right"
    />

    <router-view />
  </v-app>
</template>

<script lang="ts" setup>
  import { useMessageStore } from '@/stores/message'

  const messagesStore = useMessageStore()

  onMounted(async () => {
  //
  })
</script>
