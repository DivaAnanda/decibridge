export type RoleSlug =
  | 'admin_it'
  | 'hta_analyst'
  | 'farmasi_sekretaris'
  | 'kft_member'
  | 'ketua_kft'

export const ROLE_LABEL: Record<RoleSlug, string> = {
  admin_it: 'Admin IT',
  hta_analyst: 'HTA Analyst',
  farmasi_sekretaris: 'Sekretaris KFT',
  kft_member: 'Anggota KFT',
  ketua_kft: 'Ketua KFT',
}

export const ROLE_OPTIONS = (Object.keys(ROLE_LABEL) as RoleSlug[]).map((value) => ({
  value,
  label: ROLE_LABEL[value],
}))

export interface AdminUser {
  id: number
  email: string
  full_name: string
  nip: string
  institution: string
  roles: RoleSlug[]
  is_active: boolean
  must_change_password: boolean
  date_joined: string
  last_login: string | null
  last_login_ip: string | null
}

export interface AdminUserUpdate {
  is_active?: boolean
  roles?: RoleSlug[]
}

export interface LoginHistoryEntry {
  id: number
  created_at: string
  action: string
  action_label: string
  actor_name: string
  actor_email: string
  metadata: Record<string, unknown> | null
  ip_address: string | null
}
