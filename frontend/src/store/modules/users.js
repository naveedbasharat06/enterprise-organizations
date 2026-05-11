import {
  getUsers, getUnassignedUsers, createUser, updateUser,
  deleteUser, makeAdmin, makeMember
} from '@/api'

export default {
  namespaced: true,
  state: () => ({
    list: [],
    unassigned: [],
    loading: false,
    error: null,
  }),
  getters: {
    list: s => s.list,
    unassigned: s => s.unassigned,
    loading: s => s.loading,
    error: s => s.error,
  },
  mutations: {
    SET_LIST(state, list) { state.list = list },
    SET_UNASSIGNED(state, list) { state.unassigned = list },
    SET_LOADING(state, v) { state.loading = v },
    SET_ERROR(state, e) { state.error = e },
    ADD(state, user) { state.list.push(user) },
    UPDATE(state, user) {
      const i = state.list.findIndex(u => u.id === user.id)
      if (i !== -1) state.list.splice(i, 1, user)
    },
    REMOVE(state, id) { state.list = state.list.filter(u => u.id !== id) },
  },
  actions: {
    async fetch({ commit }) {
      commit('SET_LOADING', true)
      try {
        const { data } = await getUsers()
        commit('SET_LIST', data)
      } catch (e) {
        commit('SET_ERROR', e.response?.data?.error || 'Failed to load users')
      } finally {
        commit('SET_LOADING', false)
      }
    },
    async fetchUnassigned({ commit }) {
      const { data } = await getUnassignedUsers()
      commit('SET_UNASSIGNED', data)
    },
    async create({ commit }, payload) {
      const { data } = await createUser(payload)
      commit('ADD', data)
      return data
    },
    async update({ commit }, { id, ...payload }) {
      const { data } = await updateUser(id, payload)
      commit('UPDATE', data)
      return data
    },
    async remove({ commit }, id) {
      await deleteUser(id)
      commit('REMOVE', id)
    },
    async promoteAdmin({ commit }, id) {
      const { data } = await makeAdmin(id)
      // Re-fetch to get updated user
      return data
    },
    async demoteMember({ commit }, id) {
      const { data } = await makeMember(id)
      return data
    },
  },
}
