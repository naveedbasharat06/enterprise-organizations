import {
  getOrgs, createOrg, updateOrg, deleteOrg,
  getOrgMembers, addMemberToOrg, removeMemberFromOrg
} from '@/api'

export default {
  namespaced: true,
  state: () => ({
    list: [],
    loading: false,
    error: null,
  }),
  getters: {
    list: s => s.list,
    loading: s => s.loading,
    error: s => s.error,
  },
  mutations: {
    SET_LIST(state, list) { state.list = list },
    SET_LOADING(state, v) { state.loading = v },
    SET_ERROR(state, e) { state.error = e },
    ADD(state, org) { state.list.push(org) },
    UPDATE(state, org) {
      const i = state.list.findIndex(o => o.id === org.id)
      if (i !== -1) state.list.splice(i, 1, org)
    },
    REMOVE(state, id) { state.list = state.list.filter(o => o.id !== id) },
  },
  actions: {
    async fetch({ commit }) {
      commit('SET_LOADING', true)
      try {
        const { data } = await getOrgs()
        commit('SET_LIST', data)
      } catch (e) {
        commit('SET_ERROR', e.response?.data?.error || 'Failed to load organizations')
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async create({ commit }, payload) {
      const { data } = await createOrg(payload)
      commit('ADD', data)
      return data
    },
    async update({ commit }, { id, ...payload }) {
      const { data } = await updateOrg(id, payload)
      commit('UPDATE', data)
      return data
    },
    async remove({ commit }, id) {
      await deleteOrg(id)
      commit('REMOVE', id)
    },
    getMembers(_, id) {
      return getOrgMembers(id).then(r => r.data)
    },
    addMember(_, { orgId, userId }) {
      return addMemberToOrg(orgId, userId)
    },
    removeMember(_, { orgId, userId }) {
      return removeMemberFromOrg(orgId, userId)
    },
  },
}
