<template>
  <v-app class="bg-blue-grey-lighten-5">
    <v-snackbar-queue
      v-model="messagesStore.queue"
      location="top right"
    ></v-snackbar-queue>

    <router-view />
  </v-app>
</template>

<script lang="ts" setup>
import { useAuthStore } from "@/stores/auth";
import { useMessagesStore } from "@/stores/message";

const messagesStore = useMessagesStore();
const authStore = useAuthStore();

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    await authStore.refreshToken();
  }
});
</script>
