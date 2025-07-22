<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card class="pa-6" elevation="8" width="450">
      <v-card-title class="text-h5 text-center mb-6">{{
        t("login.form.title")
      }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="submit" class="pb-4">
          <v-text-field
            v-model="email"
            :label="t('login.form.username')"
            :rules="[rules.required, rules.email]"
            type="email"
            required
          />
          <v-text-field
            v-model="password"
            :label="t('login.form.password')"
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
            {{ t("login.form.submit") }}
          </v-btn>
          <v-card-actions>
            <v-btn class="mt-4">{{ t("login.form.newAccount") }}</v-btn>
            <v-spacer />
            <v-btn class="mt-4">{{ t("login.form.resetPassword") }}</v-btn>
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

const { t } = useI18n();
const authStore = useAuthStore();

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
  //
});
</script>
