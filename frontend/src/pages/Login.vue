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
            :label="t('common.email')"
            :rules="[validation.required, validation.email]"
            type="email"
          />
          <v-text-field
            v-model="password"
            :label="t('common.password')"
            :rules="[validation.required]"
            type="password"
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
            <v-btn class="mt-4" :to="{ name: 'register' }">{{
              t("login.form.newAccount")
            }}</v-btn>
            <v-spacer />
            <v-btn class="mt-4" :to="{ name: 'reset' }">{{
              t("login.form.resetPassword")
            }}</v-btn>
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
import { validation } from "@/plugins/validation";

const { t } = useI18n();
const authStore = useAuthStore();

const email = ref("");
const password = ref("");
const valid = ref(false);

const submit = () => {
  authStore.login(email.value, password.value, t);
};

onMounted(async () => {
  //
});
</script>
