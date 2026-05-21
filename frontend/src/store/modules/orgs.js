import {
  getOrgs, createOrg, updateOrg, deleteOrg,
  getOrgMembers, addMemberToOrg, removeMemberFromOrg,
  switchOrg, getOrgLimits,
} from '@/api'

export default {
  namespaced: true,
  state: () => ({
    list: [],
    limits: null,
    loading: false,
    error: null,
  }),
  getters: {
    list:       s => s.list,
    limits:     s => s.limits,
    loading:    s => s.loading,
    error:      s => s.error,
    ownedOrgs:  s => s.list.filter(o => o.is_owner),
    canAddMore: s => s.limits?.can_add_more ?? false,
    isPremium:  s => s.limits?.plan === 'premium',
  },
  mutations: {
    SET_LIST(state, list)     { state.list = list },
    SET_LIMITS(state, limits) { state.limits = limits },
    SET_LOADING(state, v)     { state.loading = v },
    SET_ERROR(state, e)       { state.error = e },
    ADD(state, org)           { state.list.push(org) },
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
    async fetchLimits({ commit }) {
      try {
        const { data } = await getOrgLimits()
        commit('SET_LIMITS', data)
      } catch {}
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
    async switchOrg({ dispatch }, orgId) {
      const { data: user } = await switchOrg(orgId)
      // Update auth store so sidebar and all views reflect the new active org
      dispatch('auth/updateUser', user, { root: true })
      // Re-fetch orgs and limits scoped to new active org
      await dispatch('fetch')
      await dispatch('fetchLimits')
      return user
    },
  },
}
