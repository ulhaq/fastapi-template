<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card class="pa-6" elevation="8" width="450" v-if="!newPassword">
      <v-card-title class="text-h5 text-center mb-6">{{
        t("reset.form.title")
      }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="request" class="pb-4">
          <v-text-field
            v-model="email"
            :label="t('common.email')"
            :rules="[validation.required, validation.email]"
            type="email"
          />
          <v-btn class="mb-4" color="primary" type="submit" block>
            {{ t("reset.form.submit") }}
          </v-btn>
          <v-card-actions>
            <v-btn class="mt-4" :to="{ name: 'register' }">{{
              t("reset.form.newAccount")
            }}</v-btn>
            <v-spacer />
            <v-btn class="mt-4" :to="{ name: 'login' }">{{
              t("reset.form.login")
            }}</v-btn>
          </v-card-actions>
        </v-form>
      </v-card-text>
    </v-card>
    <v-card class="pa-6" elevation="8" width="450" v-else>
      <v-card-title class="text-h5 text-center mb-6">{{
        t("reset.form.title")
      }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="reset" class="pb-4">
          <v-text-field
            v-model="password"
            :label="t('common.password')"
            :rules="[validation.required]"
            type="password"
          />
          <v-btn class="mb-4" color="primary" type="submit" block>
            {{ t("reset.form.submit") }}
          </v-btn>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref, computed } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useMessageStore } from "@/stores/message";
import { validation } from "@/plugins/validation";
import authApi from "@/apis/auth";

const route = useRoute();
const authStore = useAuthStore();
const messageStore = useMessageStore();

const { t } = useI18n();

const email = ref("");
const password = ref("");
const valid = ref(false);

const newPassword = computed(() => {
  return route.params.token;
});

const request = () => {
  authApi.requestPasswordReset(email.value);
};

const reset = async () => {
  try {
    let res = await authApi.resetPassword(password.value, route.params.token);

    console.log(res);
    authStore.login(email.value, password.value);
  } catch (err) {
    let msg;
    console.log(err);

    if (err?.response?.data?.msg) {
      msg = err.response.data.msg;
    } else if (err?.response?.data?.detail?.[0]) {
      const loc = err.response.data.detail[0].loc;
      const locPart = Array.isArray(loc) ? loc[loc.length - 1] : "";
      const detailMsg = err.response.data.detail[0].msg || "";
      msg = `${locPart} ${detailMsg}`.toLowerCase();
    } else {
      msg = err.response.data.msg;
    }
    messageStore.add({ text: msg, color: "error" });
  }
};

onMounted(async () => {
  //
});
</script>
