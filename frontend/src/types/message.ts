export interface Message {
  id: number
  text: string
  type: 'success' | 'error' | 'info' | 'warning'
  timeout?: number
}
