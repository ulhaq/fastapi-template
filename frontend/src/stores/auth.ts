// stores/auth.ts
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { useRoute } from "vue-router";
import { useMessagesStore } from "@/stores/message";
import router from "@/router";
import axios from "@/apis/base";
import authApi from "@/apis/auth";

export const useAuthStore = defineStore("auth", () => {
  const route = useRoute();
  const messages = useMessagesStore();

  const user = ref(null);
  const accessToken = ref<string | null>(null);
  const loading = ref(true);

  const isAuthenticated = computed(() => !!accessToken.value);

  function setAccessToken(token: string) {
    accessToken.value = token;
  }

  function unsetAccessToken() {
    accessToken.value = null;
  }

  async function login(email: string, password: string, t: any) {
    loading.value = true;
    try {
      const res = await authApi.getToken(email, password);
      setAccessToken(res.access_token);

      await setUser();

      const redirect = route.query.redirect;
      router.push(redirect?.startsWith("/") ? redirect : { name: "index" });
    } catch (err: any) {
      if (err?.status) {
        messages.add({ text: t("login.invalid"), color: "error" });
      } else {
        messages.add({ text: t("login.failed"), color: "error" });
      }
    } finally {
      loading.value = false;
    }
  }

  async function refreshToken() {
    loading.value = true;
    try {
      const res = await authApi.refreshToken();
      setAccessToken(res.access_token);
      await setUser();

      return res.access_token;
    } finally {
      loading.value = false;
    }
  }

  async function logout() {
    await authApi.logout();
    unsetAccessToken();
    user.value = null;
    delete axios.defaults.headers.common["Authorization"];
    router.push({ name: "login" });
  }

  async function setUser() {
    const rs = await authApi.getAuthenticatedUser();
    user.value = rs;
  }

  async function getUser() {
    return user.value;
  }

  return {
    user,
    accessToken,
    loading,
    isAuthenticated,
    login,
    refreshToken,
    logout,
    getUser,
  };
});
