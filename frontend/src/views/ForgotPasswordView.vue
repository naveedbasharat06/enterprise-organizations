<template>
  <div class="login-wrap">
    <div class="login-card">
      <div class="login-logo">⬡ RoleBase</div>
      <div class="login-sub">{{ step === 1 ? 'Reset your password' : 'Enter OTP & new password' }}</div>

      <!-- Step 1: Enter Email -->
      <template v-if="step === 1">
        <div v-if="error" class="error-msg">{{ error }}</div>
        <div v-if="successMsg" class="success-msg">{{ successMsg }}</div>
        <div class="form-group">
          <label>Email Address</label>
          <input class="form-control" type="email" v-model="email" placeholder="Enter your registered email" @keyup.enter="sendOtp" />
        </div>
        <button class="btn btn-primary btn-full" @click="sendOtp" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>Send OTP</span>
        </button>
      </template>

      <!-- Step 2: Enter OTP + New Password -->
      <template v-if="step === 2">
        <div class="info-box" style="margin-bottom:16px;">OTP sent to <strong>{{ email }}</strong>. Check your inbox.</div>
        <div v-if="error" class="error-msg">{{ error }}</div>
        <div v-if="successMsg" class="success-msg">{{ successMsg }}</div>
        <div class="form-group">
          <label>OTP Code</label>
          <input class="form-control" v-model="otp" placeholder="Enter 6-digit OTP" maxlength="6" />
        </div>
        <div class="form-group">
          <label>New Password</label>
          <input class="form-control" type="password" v-model="newPassword" placeholder="At least 8 characters" />
        </div>
        <div class="form-group">
          <label>Confirm New Password</label>
          <input class="form-control" type="password" v-model="confirmPassword" placeholder="Repeat new password" @keyup.enter="confirmReset" />
        </div>
        <button class="btn btn-primary btn-full" @click="confirmReset" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>Reset Password</span>
        </button>
        <div style="margin-top:12px;text-align:center;">
          <span class="resend-link" @click="resendOtp">Resend OTP</span>
        </div>
      </template>

      <div style="margin-top:16px;text-align:center;">
        <router-link to="/login" class="back-link">← Back to Login</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { forgotPassword, resetPasswordConfirm } from '@/api'

const route  = useRoute()
const router = useRouter()

const step            = ref(1)
const email           = ref('')
const otp             = ref('')
const newPassword     = ref('')
const confirmPassword = ref('')
const loading         = ref(false)
const error           = ref(null)
const successMsg      = ref(null)

onMounted(() => {
  if (route.query.email) email.value = route.query.email
})

async function sendOtp() {
  error.value = null; successMsg.value = null
  if (!email.value) { error.value = 'Please enter your email'; return }
  loading.value = true
  try {
    await forgotPassword(email.value)
    successMsg.value = 'OTP sent! Check your email inbox.'
    step.value = 2
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to send OTP'
  } finally { loading.value = false }
}

async function resendOtp() {
  error.value = null; successMsg.value = null
  loading.value = true
  try {
    await forgotPassword(email.value)
    successMsg.value = 'OTP resent successfully!'
  } catch (e) {
    error.value = 'Failed to resend OTP'
  } finally { loading.value = false }
}

async function confirmReset() {
  error.value = null
  if (!otp.value) { error.value = 'Please enter the OTP'; return }
  if (!newPassword.value || newPassword.value.length < 8) { error.value = 'Password must be at least 8 characters'; return }
  if (newPassword.value !== confirmPassword.value) { error.value = 'Passwords do not match'; return }
  loading.value = true
  try {
    await resetPasswordConfirm(email.value, otp.value, newPassword.value)
    successMsg.value = 'Password reset successfully! Redirecting to login...'
    setTimeout(() => router.push('/login'), 2000)
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to reset password'
  } finally { loading.value = false }
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
  border-radius: 20px; padding: 48px 40px; width: 420px; box-shadow: var(--shadow);
}
.login-logo { font-family: 'Space Grotesk', sans-serif; font-size: 24px; font-weight: 700; color: var(--accent); margin-bottom: 8px; }
.login-sub  { color: var(--text-muted); font-size: 14px; margin-bottom: 32px; }
.back-link  { font-size: 13px; color: var(--accent); text-decoration: none; }
.back-link:hover { text-decoration: underline; }
.resend-link { font-size: 13px; color: var(--accent); cursor: pointer; }
.resend-link:hover { text-decoration: underline; }
.success-msg { background: rgba(0,200,100,0.1); border: 1px solid rgba(0,200,100,0.3); color: #00c864; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; font-size: 13px; }
.info-box { background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2); border-radius: 8px; padding: 10px 14px; font-size: 13px; color: var(--text-muted); }
</style>
