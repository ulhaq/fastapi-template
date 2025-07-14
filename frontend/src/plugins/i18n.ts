import { createI18n } from "vue-i18n";
import da from "@/locales/da";
import en from "@/locales/en";

const messages = {
  en: en,
  da: da,
};

export default createI18n({
  legacy: false,
  locale: "en",
  fallbackLocale: "en",
  messages,
});
