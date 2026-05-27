import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { getMe, login as apiLogin, logout as apiLogout } from '../api/auth'
import { tokenStorage } from '../api/client'
import type { AuthUser, RoleSlug } from './types'

interface AuthContextValue {
  user: AuthUser | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  hasRole: (...slugs: RoleSlug[]) => boolean
  refresh: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refresh = useCallback(async () => {
    if (!tokenStorage.getAccess()) {
      setUser(null)
      setIsLoading(false)
      return
    }
    try {
      const me = await getMe()
      setUser(me)
    } catch {
      tokenStorage.clear()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiLogin(email, password)
    setUser(data.user)
  }, [])

  const logout = useCallback(async () => {
    await apiLogout()
    setUser(null)
  }, [])

  const hasRole = useCallback(
    (...slugs: RoleSlug[]) => {
      if (!user) return false
      if (user.is_superuser) return true
      const userSlugs = new Set(user.roles.map((r) => r.slug))
      return slugs.some((s) => userSlugs.has(s))
    },
    [user],
  )

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: user !== null,
      login,
      logout,
      hasRole,
      refresh,
    }),
    [user, isLoading, login, logout, hasRole, refresh],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
