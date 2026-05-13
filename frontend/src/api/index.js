import axios from 'axios'

const BASE = 'http://localhost:8000/api'

const api = axios.create({ baseURL: BASE })

// Attach token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

// ── AUTH ──────────────────────────────────────────────────────────────────
export const login = (username, password) =>
  api.post('/auth/login/', { username, password })

export const logout = () => api.post('/auth/logout/')

export const getMe = () => api.get('/auth/me/')

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

export const forgotPassword = (email) => api.post('/auth/forgot-password/', { email })
export const resetPasswordConfirm = (email, otp, new_password) =>
  api.post('/auth/reset-password-confirm/', { email, otp, new_password })

// ── PERMISSIONS ───────────────────────────────────────────────────────────────
export const getPermissions = () => api.get('/permissions/')
export const createPermission = data => api.post('/permissions/', data)
export const updatePermission = (id, data) => api.patch(`/permissions/${id}/`, data)
export const deletePermission = id => api.delete(`/permissions/${id}/`)

// ── ROLES ─────────────────────────────────────────────────────────────────────
export const getRoles = () => api.get('/roles/')
export const createRole = data => api.post('/roles/', data)
export const updateRole = (id, data) => api.patch(`/roles/${id}/`, data)
export const deleteRole = id => api.delete(`/roles/${id}/`)
export const assignPermissionsToRole = (id, permission_ids) =>
  api.post(`/roles/${id}/assign_permissions/`, { permission_ids })
