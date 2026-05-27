import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MantineProvider } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import App from './App'
import { AuthProvider } from './auth/AuthContext'

vi.mock('./api/client', async () => {
  const actual = await vi.importActual<typeof import('./api/client')>('./api/client')
  return {
    ...actual,
    getHealth: vi.fn().mockResolvedValue({ status: 'ok', checks: { django: 'ok', database: 'ok' } }),
  }
})

vi.mock('./api/auth', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getMe: vi.fn().mockRejectedValue(new Error('not authenticated')),
  refreshToken: vi.fn(),
}))

function renderApp(initialPath = '/') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MantineProvider>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialPath]}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    </MantineProvider>,
  )
}

describe('App routing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('redirects unauthenticated users to the login page', async () => {
    renderApp('/')
    await waitFor(() => {
      expect(screen.getByText(/Masuk ke sistem pendukung keputusan KFT/i)).toBeInTheDocument()
    })
  })

  it('renders the login form with Indonesian labels', async () => {
    renderApp('/login')
    expect(await screen.findByRole('button', { name: /Masuk/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Kata sandi/i)).toBeInTheDocument()
  })
})
