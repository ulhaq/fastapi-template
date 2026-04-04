import { createI18n } from 'vue-i18n'
import en from '@/locales/en'
import da from '@/locales/da'

const savedLocale = localStorage.getItem('locale') ?? 'en'

export const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  globalInjection: true,
  messages: { en, da },
})
