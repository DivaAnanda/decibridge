import { Navigate, useLocation } from 'react-router-dom'
import { Center, Loader } from '@mantine/core'
import type { ReactNode } from 'react'

import { useAuth } from './useAuth'
import type { RoleSlug } from './types'

interface Props {
  children: ReactNode
  roles?: RoleSlug[]
}

export function ProtectedRoute({ children, roles }: Props) {
  const { isAuthenticated, isLoading, hasRole } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <Center h="60vh">
        <Loader />
      </Center>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (roles && roles.length > 0 && !hasRole(...roles)) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
