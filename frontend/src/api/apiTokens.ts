import { apiClient } from './client'
import type { ApiTokenCreate, ApiTokenCreatedResponse, ApiTokenResponse } from '@/types'

export const apiTokensApi = {
  list() {
    return apiClient.get<ApiTokenResponse[]>('/v1/api-tokens')
  },

  create(data: ApiTokenCreate) {
    return apiClient.post<ApiTokenCreatedResponse>('/v1/api-tokens', data)
  },

  revoke(id: number) {
    return apiClient.delete(`/v1/api-tokens/${id}`)
  },
}
