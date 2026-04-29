import { useI18n } from 'vue-i18n'
import { PASSWORD_MIN_LENGTH } from '@/constants'

export type Rule = (value: string) => true | string

export function useRules() {
  const { t } = useI18n()

  return {
    required: [(v: string) => !!v.trim() || t('common.required')] as Rule[],

    email: [
      (v: string) => !!v.trim() || t('common.emailRequired'),
      (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || t('common.emailInvalid'),
    ] as Rule[],

    password: [
      (v: string) => v.length >= PASSWORD_MIN_LENGTH || t('common.passwordMinLength'),
    ] as Rule[],

    match(other: () => string): Rule[] {
      return [(v) => v === other() || t('common.passwordsDoNotMatch')]
    },
  }
}
