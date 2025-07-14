/**
 * plugins/index.ts
 *
 * Automatically included in `./src/main.ts`
 */

// Plugins
import vuetify from "./vuetify";
import pinia from "@/stores";
import router from "@/router";
import i18n from "@/plugins/i18n";

// Types
import type { App } from "vue";

import { useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";

router.beforeEach(async (to) => {
  const route = useRoute();
  const authStore = useAuthStore();

  console.log("B" + authStore.isAuthenticated);

  if (authStore.loading) {
    await new Promise<void>((resolve) => {
      const interval = setInterval(() => {
        if (!authStore.loading) {
          clearInterval(interval);
          resolve();
        }
      }, 10);
    });
  }
  console.log("B2" + authStore.isAuthenticated);

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    console.log("router auth" + to.fullPath);
    router.replace({ name: "login", query: { redirect: to.fullPath } });
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    console.log("router guest" + to.fullPath);

    const redirect = route.query.redirect;
    router.replace(redirect?.startsWith("/") ? redirect : { name: "index" });
  }
});

router.afterEach((to) => {
  const defaultTitle = "My App";
  document.title = to.meta.title || defaultTitle;
});
export function registerPlugins(app: App) {
  app.use(vuetify).use(router).use(pinia).use(i18n);
}
