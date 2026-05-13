import { getRoles, createRole, updateRole, deleteRole, assignPermissionsToRole } from '@/api'

export default {
  namespaced: true,
  state: () => ({ list: [] }),
  getters: { list: s => s.list },
  mutations: {
    SET(state, data) { state.list = data },
  },
  actions: {
    async fetch({ commit }) {
      const { data } = await getRoles()
      commit('SET', data)
    },
    async create({ dispatch }, payload) {
      await createRole(payload)
      await dispatch('fetch')
    },
    async update({ dispatch }, { id, ...payload }) {
      await updateRole(id, payload)
      await dispatch('fetch')
    },
    async remove({ dispatch }, id) {
      await deleteRole(id)
      await dispatch('fetch')
    },
    async assignPermissions({ dispatch }, { id, permission_ids }) {
      await assignPermissionsToRole(id, permission_ids)
      await dispatch('fetch')
    },
  },
}
