<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card class="pa-6" elevation="8" width="450">
      <v-card-title class="text-h5 text-center mb-6">{{
        t("login.title")
      }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="submit" class="pb-4">
          <v-text-field
            v-model="email"
            :label="t('login.email')"
            :rules="[rules.required, rules.email]"
            type="email"
            required
          />
          <v-text-field
            v-model="password"
            :label="t('login.password')"
            :rules="[rules.required]"
            type="password"
            required
          />
          <v-btn
            class="mb-4"
            color="primary"
            type="submit"
            :loading="authStore.loading"
            block
          >
            {{ t("login.login") }}
          </v-btn>
          <v-card-actions>
            <v-btn class="mt-4">{{ t("login.newAccount") }}</v-btn>
            <v-spacer />
            <v-btn class="mt-4">{{ t("login.resetPassword") }}</v-btn>
          </v-card-actions>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useRoute } from "vue-router";
import router from "@/router";

const { t } = useI18n();
const authStore = useAuthStore();
const route = useRoute();

const email = ref("");
const password = ref("");
const valid = ref(false);

const rules = {
  required: (v) => !!v || "Required",
  email: (v) => /.+@.+\..+/.test(v) || "E-mail must be valid",
};

const submit = () => {
  authStore.login(email.value, password.value, t);
};

onMounted(async () => {
  console.log("C")
  // if (authStore.isAuthenticated) {
  //   const redirect = route.query.redirect;
  //   router.replace(redirect?.startsWith("/") ? redirect : { name: "index" });
  // }
});
</script>
