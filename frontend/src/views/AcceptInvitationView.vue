<template>
  <div class="invitation-page">
    <div class="invitation-card">
      <div class="brand">⬡ RoleBase</div>

      <!-- Loading -->
      <div v-if="state === 'loading'" class="center-msg">
        <div class="spinner-lg"></div>
        <p>Validating your invitation...</p>
      </div>

      <!-- Invalid / Expired -->
      <div v-else-if="state === 'invalid'" class="center-msg">
        <div class="error-icon">✕</div>
        <h2>Invalid Invitation</h2>
        <p class="sub">{{ errorMsg }}</p>
        <router-link to="/login" class="btn btn-ghost" style="margin-top:16px;">Back to Login</router-link>
      </div>

      <!-- Success -->
      <div v-else-if="state === 'done'" class="center-msg">
        <div class="success-icon">✓</div>
        <h2>Account Created!</h2>
        <p class="sub">Your account has been set up. You can now log in.</p>
        <button class="btn btn-primary" style="margin-top:20px;" @click="goToLogin">Go to Login</button>
      </div>

      <!-- Form -->
      <div v-else-if="state === 'form'">
        <h2 class="form-title">Set Up Your Account</h2>

        <div class="invite-info">
          <div class="invite-row">
            <span class="invite-label">Email</span>
            <span class="invite-val">{{ invitation.email }}</span>
          </div>
          <div class="invite-row">
            <span class="invite-label">Role</span>
            <span class="role-badge" :class="'role-' + invitation.role">{{ formatRole(invitation.role) }}</span>
          </div>
          <div class="invite-row" v-if="invitation.organization_name">
            <span class="invite-label">Organization</span>
            <span class="invite-val">{{ invitation.organization_name }}</span>
          </div>
        </div>

        <div class="form-group">
          <label>Choose a Username *</label>
          <input class="form-control" v-model="form.username" placeholder="e.g. john_doe" autocomplete="username" />
        </div>
        <div class="form-group">
          <label>Password * <span class="hint">(min 8 characters)</span></label>
          <input class="form-control" type="password" v-model="form.password" placeholder="Create a strong password" autocomplete="new-password" />
        </div>
        <div class="form-group">
          <label>Confirm Password *</label>
          <input class="form-control" type="password" v-model="form.confirmPassword" placeholder="Repeat your password" autocomplete="new-password" />
        </div>

        <div v-if="formError" class="error-msg">{{ formError }}</div>

        <button class="btn btn-primary btn-full" @click="submit" :disabled="submitting">
          <span v-if="submitting" class="spinner"></span>
          <span v-else>Create My Account</span>
        </button>

        <div class="login-link">Already have an account? <router-link to="/login">Log in</router-link></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { getInvitation, acceptInvitation, updateAccessToken } from '@/api/index.js'

const route = useRoute()
const router = useRouter()
const store = useStore()

const state      = ref('loading')   // loading | invalid | form | done
const errorMsg   = ref('')
const formError  = ref('')
const submitting = ref(false)
const invitation = ref({})

const form = reactive({ username: '', password: '', confirmPassword: '' })

function formatRole(r) {
  return { super_admin: 'Super Admin', admin: 'Admin', member: 'Member' }[r] || r
}

onMounted(async () => {
  const token = route.query.token
  if (!token) { state.value = 'invalid'; errorMsg.value = 'No invitation token found in the link.'; return }
  try {
    const { data } = await getInvitation(token)
    invitation.value = { ...data, token }
    state.value = 'form'
  } catch (e) {
    state.value = 'invalid'
    errorMsg.value = e.response?.data?.error || 'This invitation link is invalid or has expired.'
  }
})

async function submit() {
  formError.value = ''
  if (!form.username) { formError.value = 'Username is required'; return }
  if (form.username.length < 3) { formError.value = 'Username must be at least 3 characters'; return }
  if (!form.password) { formError.value = 'Password is required'; return }
  if (form.password.length < 8) { formError.value = 'Password must be at least 8 characters'; return }
  if (form.password !== form.confirmPassword) { formError.value = 'Passwords do not match'; return }

  submitting.value = true
  try {
    await acceptInvitation({
      token: invitation.value.token,
      username: form.username,
      password: form.password,
    })
    state.value = 'done'
  } catch (e) {
    formError.value = e.response?.data?.error || 'Failed to create account. Please try again.'
  } finally {
    submitting.value = false
  }
}

function goToLogin() {
  // Clear only the browser-local session so the new user lands on the login page.
  // Does NOT call the logout API, so any admin's server-side tokens stay valid.
  updateAccessToken(null)
  localStorage.removeItem('refreshToken')
  store.commit('auth/SET_USER', null)
  router.push('/login')
}
</script>

<style scoped>
.invitation-page {
  min-height: 100vh;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.invitation-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 460px;
}
.brand {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 28px;
}
.form-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
}
.invite-info {
  background: rgba(108,99,255,.07);
  border: 1px solid rgba(108,99,255,.2);
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.invite-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}
.invite-label {
  color: var(--text-muted);
  min-width: 90px;
}
.invite-val { font-weight: 600; }
.hint { font-size: 11px; color: var(--text-muted); font-weight: 400; }
.center-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px 0;
  gap: 10px;
}
.center-msg h2 { font-size: 20px; font-weight: 700; }
.center-msg .sub { color: var(--text-muted); font-size: 14px; }
.error-icon {
  width: 52px; height: 52px; border-radius: 50%;
  background: rgba(239,68,68,.15); color: #ef4444;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700;
}
.success-icon {
  width: 52px; height: 52px; border-radius: 50%;
  background: rgba(34,197,94,.15); color: #22c55e;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700;
}
.spinner-lg {
  width: 36px; height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.btn-full { width: 100%; margin-top: 4px; }
.login-link { text-align: center; font-size: 13px; color: var(--text-muted); margin-top: 16px; }
.login-link a { color: var(--accent); text-decoration: none; }
.error-msg {
  background: rgba(239,68,68,.1); color: #ef4444;
  border: 1px solid rgba(239,68,68,.2); border-radius: 8px;
  padding: 10px 14px; font-size: 13px; margin-bottom: 12px;
}
</style>
