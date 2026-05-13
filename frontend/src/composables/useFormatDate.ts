import { useI18n } from 'vue-i18n'

export function useFormatDate() {
  const { locale } = useI18n()

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString(locale.value, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  function formatDateTime(iso: string): string {
    return new Date(iso).toLocaleString(locale.value, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return { formatDate, formatDateTime }
}
