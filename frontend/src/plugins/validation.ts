import i18n from '@/plugins/i18n'

export const validation = {
  required (v: any) {
    let result = true

    if (v === undefined || v === null) {
      result = false
    } else if (Array.isArray(v) && v.length === 0) {
      result = false
    } else {
      result = String(v).trim().length > 0
    }
    return result || i18n.global.t('rules.required')
  },
  email (v: string) {
    if (!v) {
      return true
    }

    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || i18n.global.t('rules.email')
  },
  minLength: (length: number) => (v: string) =>
    (v && v.length >= length) || i18n.global.t('rules.min', { length }),
}
