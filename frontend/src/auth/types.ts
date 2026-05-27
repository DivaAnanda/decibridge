export type RoleSlug =
  | 'admin_it'
  | 'hta_analyst'
  | 'farmasi_sekretaris'
  | 'kft_member'
  | 'ketua_kft'

export interface Role {
  slug: RoleSlug
  display_name_id: string
  display_name_en: string
  description: string
}

export interface AuthUser {
  id: number
  email: string
  full_name: string
  nip: string
  institution: string
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
  date_joined: string
  last_login: string | null
  roles: Role[]
}

export interface LoginResponse {
  access: string
  refresh: string
  user: AuthUser
}
