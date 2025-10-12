export interface Message {
  text: string
  color?: 'success' | 'error' | 'info' | 'warning'
  timeout?: number
}
