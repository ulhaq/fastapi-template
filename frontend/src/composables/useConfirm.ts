import { reactive } from 'vue'
import { i18n } from '@/plugins/i18n'

interface ConfirmState {
  open: boolean
  title: string
  description: string
  confirmLabel: string
  resolve: ((confirmed: boolean) => void) | null
}

const state = reactive<ConfirmState>({
  open: false,
  title: '',
  description: '',
  confirmLabel: '',
  resolve: null,
})

export function useConfirm() {
  function confirm(
    title: string,
    description = '',
    confirmLabel = i18n.global.t('common.confirm'),
  ): Promise<boolean> {
    return new Promise<boolean>((resolve) => {
      state.open = true
      state.title = title
      state.description = description
      state.confirmLabel = confirmLabel
      state.resolve = resolve
    })
  }

  function handleConfirm() {
    state.open = false
    state.resolve?.(true)
    state.resolve = null
  }

  function handleCancel() {
    state.open = false
    state.resolve?.(false)
    state.resolve = null
  }

  return { confirm, confirmState: state, handleConfirm, handleCancel }
}
