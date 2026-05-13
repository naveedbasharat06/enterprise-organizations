import { getPermissions, createPermission, updatePermission, deletePermission } from '@/api'

export default {
  namespaced: true,
  state: () => ({ list: [] }),
  getters: { list: s => s.list },
  mutations: {
    SET(state, data) { state.list = data },
  },
  actions: {
    async fetch({ commit }) {
      const { data } = await getPermissions()
      commit('SET', data)
    },
    async create({ dispatch }, payload) {
      await createPermission(payload)
      await dispatch('fetch')
    },
    async update({ dispatch }, { id, ...payload }) {
      await updatePermission(id, payload)
      await dispatch('fetch')
    },
    async remove({ dispatch }, id) {
      await deletePermission(id)
      await dispatch('fetch')
    },
  },
}
