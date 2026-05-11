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
