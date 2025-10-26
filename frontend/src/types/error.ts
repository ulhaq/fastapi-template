interface ErrorDetail {
  error_code: string
  field: string[]
  msg: string
  ctx: any
}

export interface APIErrorResponse {
  time: string
  path: string
  method: string
  error_code: string
  msg?: string
  errors?: ErrorDetail[]
}
