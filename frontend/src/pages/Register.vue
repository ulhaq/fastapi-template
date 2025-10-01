<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card class="pa-6" elevation="8" width="450">
      <v-card-title class="text-h5 text-center mb-6">{{
        t("register.form.title")
      }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="submit" class="pb-4">
          <v-text-field
            v-model="name"
            :label="t('common.name')"
            type="name"
            :rules="[validation.required]"
          />
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
            {{ t("register.form.submit") }}
          </v-btn>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useMessageStore } from "@/stores/message";
import { validation } from "@/plugins/validation";
import authApi from "@/apis/auth";

const { t } = useI18n();
const authStore = useAuthStore();
const messageStore = useMessageStore();

const name = ref("");
const email = ref("");
const password = ref("");
const valid = ref(false);

const submit = async () => {
  try {
    let res = await authApi.register(name.value, email.value, password.value);

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
