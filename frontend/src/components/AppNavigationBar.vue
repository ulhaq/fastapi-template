<template>
  <div>
    <v-navigation-drawer
      v-model="drawer"
      :location="$vuetify.display.mobile ? 'left' : undefined"
    >
      <v-sheet class="pt-4 pb-8 pl-4">
        <v-img
          src="https://cdn.vuetifyjs.com/docs/images/one/logos/vuetify-logo-light.png"
          cover
          aspect-ratio="16/9"
          :width="150"
        ></v-img>
      </v-sheet>
      <v-list :lines="false" density="compact" nav>
        <v-list-item
          v-for="(item, i) in items"
          :key="i"
          :value="item"
          class="pt-2 pb-2"
          :to="{ name: item.name }"
        >
          <template v-slot:prepend>
            <v-icon :icon="item.icon"></v-icon>
          </template>

          <v-list-item-title v-text="item.text"></v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar :elevation="0" class="border-b-thin">
      <v-app-bar-nav-icon
        variant="text"
        @click.stop="drawer = !drawer"
      ></v-app-bar-nav-icon>

      <v-spacer />

      <v-btn
        v-for="lang in availableLocales"
        :key="lang.key"
        @click="changeLocale(lang.key)"
      >
        {{ lang.title }}
      </v-btn>
      <v-menu>
        <template #activator="{ props }">
          <v-btn icon v-bind="props">
            <v-icon size="40">mdi-account-circle</v-icon>
          </v-btn>
        </template>

        <v-list>
          <v-list-item @click="goToProfile">
            <v-list-item-title>Profile</v-list-item-title>
          </v-list-item>
          <v-list-item @click="logout">
            <v-list-item-title>Logout</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
  </div>
</template>
<script setup>
import { ref, watch } from "vue";
import { useLocale } from "vuetify";
import { availableLocales } from "@/locales/index";
import { useAuthStore } from "@/stores/auth";

const { current } = useLocale();

const authStore = useAuthStore();

function changeLocale(locale) {
  current.value = locale;
}

const items = [
  { name: "index", text: "Home", icon: "mdi-home" },
  { name: "users", text: "Users", icon: "mdi-account-group" },
  { name: "roles", text: "Roles", icon: "mdi-shield-account" },
  { name: "permissions", text: "Permissions", icon: "mdi-shield-star" },
];

const drawer = ref(true);
const group = ref(null);

watch(group, () => {
  drawer.value = true;
});

function logout() {
  authStore.logout()
}
</script>
