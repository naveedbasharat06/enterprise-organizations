import { getStats } from '@/api'

export default {
  async fetchStats({ commit }) {
    try {
      const { data } = await getStats()
      commit('SET_STATS', data)
    } catch {}
  },
  showToast({ commit }, { message, type = 'success' }) {
    commit('SET_TOAST', { message, type })
    setTimeout(() => commit('HIDE_TOAST'), 3200)
  },
}
