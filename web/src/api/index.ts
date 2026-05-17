const BASE_URL = import.meta.env.VITE_API_BASE || ''

function getToken(): string | null {
  return localStorage.getItem('admin_token')
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (res.status === 401) {
    localStorage.removeItem('admin_token')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (res.status === 204) return undefined as T

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const err = new Error(body.detail || `HTTP ${res.status}`) as any
    err.status = res.status
    throw err
  }

  return res.json()
}

export const api = {
  login(adminKey: string) {
    return request<{ success: boolean; token: string }>('/admin/auth/login', {
      method: 'POST',
      body: JSON.stringify({ admin_key: adminKey }),
    })
  },

  getPlatforms() {
    return request<PlatformInfo[]>('/admin/platforms')
  },

  getStats() {
    return request<PlatformStats[]>('/admin/stats')
  },

  getQuotaOverview() {
    return request<QuotaOverviewItem[]>('/admin/stats/quota/overview')
  },

  getKeys(page = 1, pageSize = 20, platform?: string, status?: string) {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
    if (platform) params.set('platform', platform)
    if (status) params.set('status', status)
    return request<Paginated<KeyItem>>(`/admin/keys?${params}`)
  },
  createKey(data: { platform: string; api_key: string; weight?: number }) {
    return request<KeyItem>('/admin/keys', { method: 'POST', body: JSON.stringify(data) })
  },
  updateKey(id: number, data: { weight?: number; status?: string }) {
    return request<KeyItem>(`/admin/keys/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
  },
  deleteKey(id: number) {
    return request<void>(`/admin/keys/${id}`, { method: 'DELETE' })
  },
  getKeyQuota(id: number) {
    return request<{ supported: boolean; remaining: number | null; raw: any }>(`/admin/keys/${id}/quota`)
  },
  batchDeleteKeys(ids: number[]) {
    return Promise.all(ids.map(id => api.deleteKey(id)))
  },
  batchUpdateKeys(ids: number[], data: { status?: string }) {
    return Promise.all(ids.map(id => api.updateKey(id, data)))
  },

  getProxies(page = 1, pageSize = 20) {
    return request<Paginated<ProxyItem>>(`/admin/proxies?page=${page}&page_size=${pageSize}`)
  },
  createProxy(data: { protocol: string; host: string; port: number; username?: string; password?: string }) {
    return request<ProxyItem>('/admin/proxies', { method: 'POST', body: JSON.stringify(data) })
  },
  updateProxy(id: number, data: Record<string, unknown>) {
    return request<ProxyItem>(`/admin/proxies/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
  },
  deleteProxy(id: number) {
    return request<void>(`/admin/proxies/${id}`, { method: 'DELETE' })
  },
  batchDeleteProxies(ids: number[]) {
    return Promise.all(ids.map(id => api.deleteProxy(id)))
  },
  batchUpdateProxies(ids: number[], data: Record<string, unknown>) {
    return Promise.all(ids.map(id => api.updateProxy(id, data)))
  },

  getTokens(page = 1, pageSize = 20) {
    return request<Paginated<TokenItem>>(`/admin/tokens?page=${page}&page_size=${pageSize}`)
  },
  createToken(data: { name: string; allowed_platforms: string[] }) {
    return request<TokenItem>('/admin/tokens', { method: 'POST', body: JSON.stringify(data) })
  },
  updateToken(id: number, data: { name?: string; allowed_platforms?: string[]; status?: string }) {
    return request<TokenItem>(`/admin/tokens/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
  },
  deleteToken(id: number) {
    return request<void>(`/admin/tokens/${id}`, { method: 'DELETE' })
  },
  batchDeleteTokens(ids: number[]) {
    return Promise.all(ids.map(id => api.deleteToken(id)))
  },
  batchUpdateTokens(ids: number[], data: { status?: string }) {
    return Promise.all(ids.map(id => api.updateToken(id, data)))
  },
}

export interface PlatformInfo {
  name: string
  enabled: boolean
  quota_supported: boolean
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface PlatformStats {
  platform: string
  total_keys: number
  active_keys: number
  total_requests: number
  failed_requests: number
  active_sessions: number
}

export interface KeyItem {
  id: number
  platform: string
  api_key: string
  weight: number
  status: string
  total_requests: number
  failed_requests: number
  last_used_at: string | null
  quota_remaining: number | null
  quota_updated_at: string | null
  created_at: string
}

export interface ProxyItem {
  id: number
  protocol: string
  host: string
  port: number
  username: string | null
  password: string | null
  status: string
  created_at: string
}

export interface TokenItem {
  id: number
  name: string
  token_value: string
  allowed_platforms: string[]
  status: string
  created_at: string
}

export interface QuotaOverviewItem {
  platform: string
  keys: { id: number; remaining: number }[]
  avg_remaining: number | null
}
