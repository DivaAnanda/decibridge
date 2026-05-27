import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

const ACCESS_TOKEN_KEY = 'decibridge.accessToken'
const REFRESH_TOKEN_KEY = 'decibridge.refreshToken'

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  },
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess()
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

// Refresh-on-401: try once with the refresh token, then bail.
let refreshInflight: Promise<string> | null = null

async function performRefresh(): Promise<string> {
  if (!refreshInflight) {
    const refresh = tokenStorage.getRefresh()
    if (!refresh) throw new Error('No refresh token')
    refreshInflight = axios
      .post<{ access: string }>(`${API_BASE_URL}/auth/refresh/`, { refresh })
      .then(({ data }) => {
        tokenStorage.set(data.access, refresh)
        return data.access
      })
      .finally(() => {
        refreshInflight = null
      })
  }
  return refreshInflight
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (AxiosRequestConfig & { _retried?: boolean }) | undefined
    const status = error.response?.status

    if (status === 401 && original && !original._retried) {
      const url = original.url ?? ''
      if (url.includes('/auth/login/') || url.includes('/auth/refresh/')) {
        tokenStorage.clear()
        return Promise.reject(error)
      }
      try {
        const newAccess = await performRefresh()
        original._retried = true
        original.headers = { ...(original.headers ?? {}), Authorization: `Bearer ${newAccess}` }
        return apiClient.request(original)
      } catch {
        tokenStorage.clear()
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  },
)

export interface HealthResponse {
  status: 'ok' | 'degraded'
  checks: Record<string, string>
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health/')
  return data
}
