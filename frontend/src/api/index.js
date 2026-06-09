import axios from 'axios'

// Dev: uses VITE_API_URL from .env.development → http://localhost:8000/api
// Docker: VITE_API_URL is /api, proxied by Nginx to the backend container
const BASE = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({ baseURL: BASE })

// Separate instance for refresh calls — no interceptors, prevents infinite loop
const refreshApi = axios.create({ baseURL: BASE })

// In-memory access token (more secure than localStorage — not readable by XSS)
let _accessToken = null
export function updateAccessToken(token) { _accessToken = token }

// Attach Bearer token to every request
api.interceptors.request.use(config => {
  if (_accessToken) config.headers.Authorization = `Bearer ${_accessToken}`
  return config
})

// On 401: try to refresh the access token, then retry the original request
api.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        try {
          const { data } = await refreshApi.post('/auth/token/refresh/', { refresh: refreshToken })
          updateAccessToken(data.access)
          if (data.refresh) localStorage.setItem('refreshToken', data.refresh)
          original.headers.Authorization = `Bearer ${data.access}`
          return api(original)
        } catch {
          updateAccessToken(null)
          localStorage.removeItem('refreshToken')
          window.location.href = '/login'
        }
      } else {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// ── AUTH ──────────────────────────────────────────────────────────────────
export const login = (username, password) =>
  api.post('/auth/login/', { username, password })

export const logout = (refresh) => api.post('/auth/logout/', { refresh })

export const getMe = () => api.get('/auth/me/')

export const refreshTokens = (refresh) =>
  refreshApi.post('/auth/token/refresh/', { refresh })

export const getMyRoles = () => api.get('/auth/me/roles/')
export const getMyDirectPermissions = () => api.get('/auth/me/permissions/')

export const inviteUser = (data) => api.post('/auth/invite/', data)
export const getInvitation = (token) => api.get(`/auth/accept-invitation/?token=${token}`)
export const acceptInvitation = (data) => api.post('/auth/accept-invitation/', data)

export const forgotPassword = (email) => api.post('/auth/forgot-password/', { email })
export const resetPasswordConfirm = (email, otp, new_password) =>
  api.post('/auth/reset-password-confirm/', { email, otp, new_password })

// ── DASHBOARD ─────────────────────────────────────────────────────────────
export const getStats = () => api.get('/dashboard/stats/')

// ── ORGANIZATIONS ─────────────────────────────────────────────────────────
export const getOrgs = () => api.get('/organizations/')
export const createOrg = data => api.post('/organizations/', data)
export const updateOrg = (id, data) => api.patch(`/organizations/${id}/`, data)
export const deleteOrg = id => api.delete(`/organizations/${id}/`)
export const getOrgMembers = id => api.get(`/organizations/${id}/members/`)
export const addMemberToOrg = (id, user_id) =>
  api.post(`/organizations/${id}/add_member/`, { user_id })
export const removeMemberFromOrg = (id, user_id) =>
  api.post(`/organizations/${id}/remove_member/`, { user_id })
export const switchOrg    = id => api.post(`/organizations/${id}/switch_org/`)
export const getOrgLimits = ()  => api.get('/organizations/my_limits/')
export const approveOrg   = id  => api.post(`/organizations/${id}/approve/`)
export const rejectOrg    = id  => api.post(`/organizations/${id}/reject/`)

// ── USERS ─────────────────────────────────────────────────────────────────
export const getUsers = () => api.get('/users/')
export const getUnassignedUsers = () => api.get('/users/unassigned/')
export const createUser = data => api.post('/users/', data)
export const updateUser = (id, data) => api.patch(`/users/${id}/`, data)
export const deleteUser = id => api.delete(`/users/${id}/`)
export const makeAdmin = id => api.post(`/users/${id}/make_admin/`)
export const makeMember = id => api.post(`/users/${id}/make_member/`)
export const getUserRoles = id => api.get(`/users/${id}/roles/`)
export const assignRole = (id, role_id) => api.post(`/users/${id}/assign_role/`, { role_id })
export const removeRole = (id, role_id) => api.post(`/users/${id}/remove_role/`, { role_id })
export const getUserDirectPermissions = id => api.get(`/users/${id}/direct_permissions/`)
export const assignPermissionToUser = (id, permission_id) => api.post(`/users/${id}/assign_permission/`, { permission_id })
export const removePermissionFromUser = (id, permission_id) => api.post(`/users/${id}/remove_permission/`, { permission_id })

// ── PERMISSIONS ───────────────────────────────────────────────────────────
export const getPermissions = () => api.get('/permissions/')
export const createPermission = data => api.post('/permissions/', data)
export const updatePermission = (id, data) => api.patch(`/permissions/${id}/`, data)
export const deletePermission = id => api.delete(`/permissions/${id}/`)

// ── ROLES ─────────────────────────────────────────────────────────────────
export const getRoles = () => api.get('/roles/')
export const createRole = data => api.post('/roles/', data)
export const updateRole = (id, data) => api.patch(`/roles/${id}/`, data)
export const deleteRole = id => api.delete(`/roles/${id}/`)
export const assignPermissionsToRole = (id, permission_ids) =>
  api.post(`/roles/${id}/assign_permissions/`, { permission_ids })

// ── RECORDINGS ────────────────────────────────────────────────────────────
export const getRecordings = () => api.get('/recordings/')
export const uploadRecording = (formData) =>
  api.post('/recordings/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const deleteRecording = id => api.delete(`/recordings/${id}/`)
export const toggleOrgRecording = id => api.post(`/organizations/${id}/toggle_recording/`)
export const toggleOrgActive    = id => api.post(`/organizations/${id}/toggle_active/`)

// ── AI ────────────────────────────────────────────────────────────────────
export const onboardingChat = (message, history) =>
  axios.post(`${BASE}/ai/onboarding-chat/`, { message, history })

// ── PAYMENTS (public — no auth token needed) ──────────────────────────────
const publicApi = axios.create({ baseURL: BASE })

export const createCheckoutSession = (data) =>
  publicApi.post('/payments/create-checkout-session/', data)

// ── PAYMENTS (authenticated) ──────────────────────────────────────────────
export const getSubscriptionStatus = () => api.get('/payments/subscription-status/')
export const getStorageUsage       = () => api.get('/payments/storage-usage/')
