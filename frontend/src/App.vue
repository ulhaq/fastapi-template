<template>
  <v-app>
    <v-snackbar-queue
      v-model="messagesStore.queue"
      location="top right"
    ></v-snackbar-queue>

    <router-view v-if="!authStore.loading" />

    <v-overlay class="align-center justify-center" :model-value="true" v-else>
      <v-progress-circular
        color="primary"
        size="75"
        indeterminate
      ></v-progress-circular>
    </v-overlay>
  </v-app>
</template>

<script lang="ts" setup>
import { useAuthStore } from "@/stores/auth";
import { useMessagesStore } from "@/stores/message";

const messagesStore = useMessagesStore();
const authStore = useAuthStore();

onMounted(async () => {
  console.log("A");
  if (!authStore.isAuthenticated) {
    console.log("A Refreshing");
    await authStore.refreshToken();
    console.log("A RefreshingDONE");
  }
});
</script>
