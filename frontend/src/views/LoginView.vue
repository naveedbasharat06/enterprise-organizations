<template>
  <div class="login-wrap">
    <div class="login-card">
      <div class="login-logo">⬡ RoleBase</div>
      <div class="login-sub">Role-based dashboard system</div>

      <div v-if="pendingVerification" class="verification-notice">
        <div class="notice-icon">🔐</div>
        <div class="notice-text">
          <strong>Verification Pending</strong>
          <p>Your organization is pending Super Admin approval. You cannot log in until verified.</p>
        </div>
      </div>

      <div v-else-if="error" class="error-msg">{{ error }}</div>

      <div class="form-group">
        <label>Username</label>
        <input class="form-control" v-model="form.username" @keyup.enter="submit" placeholder="Enter username" />
      </div>
      <div class="form-group">
        <label>Password</label>
        <input class="form-control" type="password" v-model="form.password" @keyup.enter="submit" placeholder="Enter password" />
      </div>

      <button class="btn btn-primary btn-full" @click="submit" :disabled="loading">
        <span v-if="loading" class="spinner"></span>
        <span v-else>Sign In</span>
      </button>

      <div style="margin-top:16px;text-align:center;">
        <router-link to="/forgot-password" class="forgot-link">Forgot Password?</router-link>
      </div>

      <div style="margin-top:12px;font-size:12px;color:var(--text-muted);text-align:center;">
        superadmin / Admin@1234 &nbsp;|&nbsp; admin_tech / Admin@1234 &nbsp;|&nbsp; john_member / Admin@1234
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store  = useStore()
const router = useRouter()

const form                = reactive({ username: '', password: '' })
const loading             = computed(() => store.getters['auth/loading'])
const error               = computed(() => store.getters['auth/error'])
const pendingVerification = computed(() => store.getters['auth/pendingVerification'])

async function submit() {
  const ok = await store.dispatch('auth/login', form)
  if (ok) router.push('/')
}
</script>

<style scoped>
.login-wrap {
  display: flex; align-items: center; justify-content: center; min-height: 100vh;
  background: radial-gradient(ellipse at 30% 40%, #1a1060 0%, transparent 60%),
              radial-gradient(ellipse at 70% 80%, #002e24 0%, transparent 55%), var(--bg);
}
.login-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 20px; padding: 48px 40px; width: 400px; box-shadow: var(--shadow);
}
.login-logo { font-family: 'Space Grotesk', sans-serif; font-size: 24px; font-weight: 700; color: var(--accent); margin-bottom: 8px; }
.login-sub  { color: var(--text-muted); font-size: 14px; margin-bottom: 32px; }
.forgot-link { font-size: 13px; color: var(--accent); text-decoration: none; }
.forgot-link:hover { text-decoration: underline; }

.verification-notice {
  display: flex; align-items: flex-start; gap: 12px;
  background: rgba(245,158,11,.08); border: 1.5px solid #f59e0b;
  border-radius: 10px; padding: 14px 16px; margin-bottom: 20px;
}
.notice-icon { font-size: 20px; flex-shrink: 0; }
.notice-text strong { display: block; font-size: 13px; font-weight: 700; color: #f59e0b; margin-bottom: 4px; }
.notice-text p { font-size: 12px; color: var(--text-muted); margin: 0; line-height: 1.5; }
</style>
