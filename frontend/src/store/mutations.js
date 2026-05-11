export default {
  SET_STATS(state, stats) { state.stats = stats },
  SET_TOAST(state, { message, type }) {
    state.toast = { message, type, show: true }
  },
  HIDE_TOAST(state) {
    state.toast = { ...state.toast, show: false }
  },
}
