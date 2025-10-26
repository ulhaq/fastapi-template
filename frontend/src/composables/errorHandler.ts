import type { APIErrorResponse } from '@/types/error'
import i18n from '@/plugins/i18n'
import { useMessageStore } from '@/stores/message'

const errorsWithExtendedTimeout = new Set([
  'unauthorized',
  'permission_denied',
  'token_expired',
  'token_invalid',
  'signature_expired',
  'signature_invalid',
])

export function useErrorHandler (data: APIErrorResponse, context?: any): void {
  const messageStore = useMessageStore()
  const { te, t } = i18n.global

  const addError = (text: string, timeout?: number) => {
    messageStore.add({ text, type: 'error', timeout: timeout || 3000 })
  }

  const resolveTimeOut = (code?: string) => {
    return (code && errorsWithExtendedTimeout.has(code)) ? 5000 : 0
  }

  const resolveErrorMessage = (code?: string, fallback?: string, ctx: Record<string, any> = {}) => {
    const key = code ? `errors.api.${code}` : ''

    if (code && te(key)) {
      return t(key, ctx)
    } else if (code && te(key, i18n.global.fallbackLocale.value)) {
      return i18n.global.t(key, ctx, i18n.global.fallbackLocale.value)
    }

    return fallback || t('errors.common')
  }

  if (data.msg) {
    addError(
      resolveErrorMessage(data.error_code, data.msg, context),
      resolveTimeOut(data.error_code),
    )
    return
  }

  if (Array.isArray(data.errors) && data.errors.length > 0) {
    for (const err of data.errors) {
      const ctx = {
        field: err.field?.length
          ? t(`errors.fields.${err.field.join(',')}`)
          : undefined,
        ...err.ctx,
        ...context,
      }
      addError(
        resolveErrorMessage(err.error_code, err.ctx?.reason, ctx),
        resolveTimeOut(err.error_code),
      )
    }
    return
  }

  addError(t('errors.common'))
}
