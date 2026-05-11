import { createStore } from 'vuex'
import mutations from './mutations'
import actions from './actions'
import auth from './modules/auth'
import orgs from './modules/orgs'
import users from './modules/users'

export default createStore({
  state: () => ({
    stats: null,
    toast: { show: false, message: '', type: 'success' },
  }),
  mutations,
  actions,
  modules: { auth, orgs, users },
})
