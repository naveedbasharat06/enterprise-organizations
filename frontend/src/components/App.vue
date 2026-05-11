<template>
  <router-view />
  <!-- Global Toast -->
  <div v-if="toast.show" class="toast" :class="toast.type">
    {{ toast.message }}
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'

const store = useStore()
const toast = computed(() => store.state.toast)
</script>
