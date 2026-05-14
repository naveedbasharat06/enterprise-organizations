import { login, logout, getMe, refreshTokens, updateAccessToken } from '@/api'

export default {
  namespaced: true,
  state: () => ({
    user: null,
    loading: false,
    error: null,
  }),
  getters: {
    isLoggedIn:  s => !!s.user,
    isSuperAdmin: s => s.user?.role === 'super_admin',
    isAdmin:     s => ['super_admin', 'admin'].includes(s.user?.role),
    isMember:    s => s.user?.role === 'member',
    user:        s => s.user,
    loading:     s => s.loading,
    error:       s => s.error,
  },
  mutations: {
    SET_USER(state, user)    { state.user = user },
    SET_LOADING(state, v)    { state.loading = v },
    SET_ERROR(state, e)      { state.error = e },
  },
  actions: {
    async login({ commit }, { username, password }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      try {
        const { data } = await login(username, password)
        // access token lives in memory only (XSS-safe)
        updateAccessToken(data.access)
        // refresh token persists across page reloads
        localStorage.setItem('refreshToken', data.refresh)
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
      const refresh = localStorage.getItem('refreshToken')
      try { await logout(refresh) } catch {}
      updateAccessToken(null)
      localStorage.removeItem('refreshToken')
      commit('SET_USER', null)
    },

    async restoreSession({ commit }) {
      const refresh = localStorage.getItem('refreshToken')
      if (!refresh) return
      try {
        // use refresh token to get a new access token
        const { data: tokenData } = await refreshTokens(refresh)
        updateAccessToken(tokenData.access)
        // if server rotated the refresh token, save the new one
        if (tokenData.refresh) localStorage.setItem('refreshToken', tokenData.refresh)
        // fetch the current user profile
        const { data: user } = await getMe()
        commit('SET_USER', user)
      } catch {
        // refresh token expired or invalid — force re-login
        updateAccessToken(null)
        localStorage.removeItem('refreshToken')
        commit('SET_USER', null)
      }
    },

    updateUser({ commit }, user) {
      commit('SET_USER', user)
    },
  },
}
