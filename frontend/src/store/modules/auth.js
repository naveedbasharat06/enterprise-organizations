import { login, logout, getMe } from '@/api'

export default {
  namespaced: true,
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null,
  }),
  getters: {
    isLoggedIn: s => !!s.user,
    isSuperAdmin: s => s.user?.role === 'super_admin',
    isAdmin: s => ['super_admin', 'admin'].includes(s.user?.role),
    isMember: s => s.user?.role === 'member',
    user: s => s.user,
    loading: s => s.loading,
    error: s => s.error,
  },
  mutations: {
    SET_USER(state, user) { state.user = user },
    SET_TOKEN(state, token) {
      state.token = token
      if (token) localStorage.setItem('token', token)
      else localStorage.removeItem('token')
    },
    SET_LOADING(state, v) { state.loading = v },
    SET_ERROR(state, e) { state.error = e },
  },
  actions: {
    async login({ commit }, { username, password }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      try {
        const { data } = await login(username, password)
        commit('SET_TOKEN', data.token)
        commit('SET_USER', data.user)
        return true
      } catch (e) {
        commit('SET_ERROR', e.response?.data?.error || 'Login failed')
        return false
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async logout({ commit }) {
      try { await logout() } catch {}
      commit('SET_TOKEN', null)
      commit('SET_USER', null)
    },
    async restoreSession({ commit, state }) {
      if (!state.token) return
      try {
        const { data } = await getMe()
        commit('SET_USER', data)
      } catch {
        commit('SET_TOKEN', null)
        commit('SET_USER', null)
      }
    },
    updateUser({ commit }, user) {
      commit('SET_USER', user)
    },
  },
}
