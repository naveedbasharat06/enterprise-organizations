<template>
  <div class="success-page">
    <div class="success-card">

      <!-- Loading state -->
      <template v-if="status === 'loading'">
        <div class="loading-icon">⏳</div>
        <h1 class="success-title">Setting up your account…</h1>
        <p class="success-sub">Please wait while we activate your subscription.</p>
      </template>

      <!-- Success state -->
      <template v-else-if="status === 'success' || status === 'already_completed'">
        <div class="success-icon">🎉</div>
        <h1 class="success-title">You're all set!</h1>
        <p class="success-sub">Your organization has been created and your subscription is active.</p>

        <div class="creds-box" v-if="accountInfo.username">
          <div class="creds-title">Your Login Details</div>
          <div class="cred-row">
            <span class="cred-label">Username</span>
            <span class="cred-value">{{ accountInfo.username }}</span>
          </div>
          <div class="cred-row">
            <span class="cred-label">Email</span>
            <span class="cred-value">{{ accountInfo.email }}</span>
          </div>
          <div class="cred-row">
            <span class="cred-label">Plan</span>
            <span class="cred-value" style="text-transform:capitalize">{{ accountInfo.plan }}</span>
          </div>
          <div class="cred-row">
            <span class="cred-label">Password</span>
            <span class="cred-value">The password you entered during signup</span>
          </div>
        </div>

        <div class="next-steps">
          <div class="next-title">What to do next</div>
          <ol class="next-list">
            <li>Log in with your email and password</li>
            <li>Go to <strong>Organizations</strong> to view your org settings</li>
            <li>Go to <strong>Roles</strong> to create custom roles</li>
            <li>Go to <strong>Users</strong> to invite team members</li>
            <li>Assign roles and permissions to your members</li>
          </ol>
        </div>

        <button class="btn btn-primary btn-lg" @click="goToLogin">Go to Login →</button>
      </template>

      <!-- Error state -->
      <template v-else-if="status === 'error'">
        <div class="error-icon">❌</div>
        <h1 class="success-title">Something went wrong</h1>
        <p class="success-sub">{{ errorMessage }}</p>
        <button class="btn btn-ghost btn-lg" @click="$router.push('/onboarding')">← Try Again</button>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import axios from 'axios'

const router       = useRouter()
const route        = useRoute()
const store        = useStore()
const status       = ref('loading')
const errorMessage = ref('')
const accountInfo  = ref({})

const BASE = import.meta.env.VITE_API_URL || '/api'

async function verifySession() {
  const sessionId = route.query.session_id
  if (!sessionId) {
    status.value = 'error'
    errorMessage.value = 'No session ID found. Please try the onboarding again.'
    return
  }

  try {
    const { data } = await axios.get(`${BASE}/payments/verify-session/?session_id=${sessionId}`)
    if (data.status === 'success' || data.status === 'already_completed') {
      accountInfo.value = { username: data.username, email: data.email, plan: data.plan }
      status.value = 'success'
    } else if (data.status === 'pending') {
      status.value = 'error'
      errorMessage.value = 'Payment is still processing. Please wait a moment and refresh the page.'
    }
  } catch (e) {
    status.value = 'error'
    const detail = e.response?.data?.error || e.response?.data?.detail || e.message || 'Unknown error'
    errorMessage.value = `Error ${e.response?.status || ''}: ${detail}`
  }
}

async function goToLogin() {
  // Log out any currently active session so the router guard doesn't
  // redirect an already-logged-in user back to their dashboard instead of login.
  await store.dispatch('auth/logout')
  router.push('/login')
}

onMounted(() => verifySession())
</script>

<style scoped>
.success-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 32px 16px; background: var(--bg); }

.success-card { background: var(--surface); border: 1.5px solid var(--border); border-radius: 20px; padding: 48px 40px; max-width: 520px; width: 100%; text-align: center; }

.success-icon  { font-size: 64px; margin-bottom: 16px; }
.success-title { font-size: 28px; font-weight: 800; margin: 0 0 10px; }
.success-sub   { color: var(--text-muted); font-size: 15px; margin-bottom: 32px; }

.creds-box   { background: var(--bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: left; margin-bottom: 28px; }
.creds-title { font-size: 13px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 14px; }
.cred-row    { display: flex; gap: 12px; margin-bottom: 8px; font-size: 14px; }
.cred-label  { color: var(--text-muted); min-width: 80px; font-weight: 500; }
.cred-value  { color: var(--text); font-weight: 600; word-break: break-all; }

.next-steps  { text-align: left; background: var(--bg); border-radius: 12px; padding: 20px; margin-bottom: 28px; }
.next-title  { font-size: 14px; font-weight: 700; margin-bottom: 12px; }
.next-list   { margin: 0; padding-left: 20px; display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: var(--text-muted); line-height: 1.5; }
.next-list strong { color: var(--text); }

.btn-lg { padding: 14px 32px; font-size: 16px; width: 100%; }
</style>
