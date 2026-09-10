import { apiClient } from './client'
import type { AdminUser, AdminUserUpdate, LoginHistoryEntry } from '../admin/types'

export async function listUsers(params?: {
  search?: string
  is_active?: 'true' | 'false'
}): Promise<AdminUser[]> {
  const { data } = await apiClient.get<AdminUser[]>('/admin/users/', { params })
  return data
}

export async function updateUser(
  userId: number,
  payload: AdminUserUpdate,
): Promise<AdminUser> {
  const { data } = await apiClient.patch<AdminUser>(`/admin/users/${userId}/`, payload)
  return data
}

export async function forcePasswordReset(userId: number): Promise<AdminUser> {
  const { data } = await apiClient.post<AdminUser>(
    `/admin/users/${userId}/force-password-reset/`,
  )
  return data
}

export async function listLoginHistory(params?: {
  only_failed?: 'true'
  user_id?: number
}): Promise<LoginHistoryEntry[]> {
  const { data } = await apiClient.get<LoginHistoryEntry[]>('/admin/login-history/', {
    params,
  })
  return data
}
