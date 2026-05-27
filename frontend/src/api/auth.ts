import { apiClient, tokenStorage } from './client'
import type { AuthUser, LoginResponse } from '../auth/types'

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/auth/login/', { email, password })
  tokenStorage.set(data.access, data.refresh)
  return data
}

export async function logout(): Promise<void> {
  const refresh = tokenStorage.getRefresh()
  try {
    if (refresh) {
      await apiClient.post('/auth/logout/', { refresh })
    }
  } finally {
    tokenStorage.clear()
  }
}

export async function getMe(): Promise<AuthUser> {
  const { data } = await apiClient.get<AuthUser>('/auth/me/')
  return data
}

export async function refreshToken(): Promise<string> {
  const refresh = tokenStorage.getRefresh()
  if (!refresh) throw new Error('No refresh token')
  const { data } = await apiClient.post<{ access: string }>('/auth/refresh/', { refresh })
  const currentRefresh = tokenStorage.getRefresh() ?? refresh
  tokenStorage.set(data.access, currentRefresh)
  return data.access
}
