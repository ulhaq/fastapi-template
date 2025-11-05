import i18n from '@/plugins/i18n'
import { useMessageStore } from '@/stores/message'

const errorsWithTimeout = new Set([
  'server_error',
  'login_failed',
  'unauthorized',
  'permission_denied',
  'token_expired',
  'token_invalid',
  'signature_expired',
  'signature_invalid',
  'resource_not_found',
  'resource_already_exists',
])

export function useErrorHandler (errorResponse: any, context?: any): void {
  const messageStore = useMessageStore()
  const { te, t } = i18n.global

  const addError = (text: string, timeout?: number) => {
    messageStore.add({ text, type: 'error', timeout })
  }

  const resolveTimeOut = (code?: string) => {
    return (code && errorsWithTimeout.has(code)) ? 5000 : 0
  }

  const resolveErrorMessage = (code?: string, fallback?: string, ctx: Record<string, any> = {}) => {
    const key = code ? `errors.api.${code}` : ''

    if (code && te(key)) {
      return t(key, ctx)
    } else if (code && te(key, i18n.global.fallbackLocale.value)) {
      return t(key, ctx, i18n.global.fallbackLocale.value)
    }

    return fallback || t('errors.common')
  }

  const resolveFieldLabel = (field: Array<string | number>) => {
    if (!Array.isArray(field) || field.length === 0) {
      return undefined
    }

    if (te(`errors.fields.${field.join(',')}`, i18n.global.fallbackLocale.value)) {
      return t(`errors.fields.${field.join(',')}`, i18n.global.fallbackLocale.value)
    }

    const alphabet = 'abcdefghijklmnopqrstuvwxyz'
    const ctx: Record<string, number> = {}
    let placeholderIndex = 0

    const keyParts = field.map(part => {
      if (typeof part === 'number' || !Number.isNaN(Number(part))) {
        const key = alphabet[placeholderIndex++]
        ctx[key] = Number(part)
        return key
      }
      return part
    })

    const i18nKey = `errors.fields.${keyParts.join(',')}`

    if (te(i18nKey, i18n.global.fallbackLocale.value)) {
      return t(i18nKey, ctx, i18n.global.fallbackLocale.value)
    }

    const fallbackField = field
      .map(part => (typeof part === 'number' ? `[${part}]` : part))
      .join('.')

    return fallbackField
  }

  if (errorResponse.response.data.msg) {
    addError(
      resolveErrorMessage(
        errorResponse.response.data.error_code,
        errorResponse.response.data.msg,
        context,
      ),
      resolveTimeOut(errorResponse.response.data.error_code),
    )
    return
  }

  if (Array.isArray(errorResponse.response.data.errors) && errorResponse.response.data.errors.length > 0) {
    for (const err of errorResponse.response.data.errors) {
      const ctx = {
        field: resolveFieldLabel(err.field),
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
