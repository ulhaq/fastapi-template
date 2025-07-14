/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import "@mdi/font/css/materialdesignicons.css";
import "vuetify/styles";
import { createVuetify } from "vuetify";
import { createVueI18nAdapter } from "vuetify/locale/adapters/vue-i18n";
import i18n from '@/plugins/i18n'
import { useI18n } from "vue-i18n";


export default createVuetify({
  theme: {},
  locale: {
    adapter: createVueI18nAdapter({ i18n, useI18n }),
  },
});
