export interface Message {
  time: number
  text: string
  type: 'success' | 'error' | 'info' | 'warning'
  timeout?: number
}
