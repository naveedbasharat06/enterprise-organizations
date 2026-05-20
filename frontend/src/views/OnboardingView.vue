<template>
  <div class="onboarding-page">
    <div class="onboarding-card">
      <!-- Header -->
      <div class="ob-logo">RoleBase</div>
      <div class="step-indicator">
        <div v-for="n in 3" :key="n" class="step-dot" :class="{ active: step >= n, done: step > n }">
          <span>{{ step > n ? '✓' : n }}</span>
        </div>
        <div class="step-line" :style="{ width: ((step - 1) / 2 * 100) + '%' }"></div>
      </div>
      <div class="step-label">Step {{ step }} of 3 — {{ stepLabels[step - 1] }}</div>

      <!-- Step 1: Organization Details -->
      <div v-if="step === 1" class="step-body">
        <div class="field-group">
          <label>Organization Name *</label>
          <input v-model="form.org_name" type="text" placeholder="e.g. Acme Corp" class="field-input" />
        </div>
        <div class="field-row">
          <div class="field-group">
            <label>Industry / Sector *</label>
            <select v-model="form.org_type" class="field-input">
              <option value="technology">Technology</option>
              <option value="healthcare">Healthcare</option>
              <option value="education">Education</option>
              <option value="finance">Finance</option>
              <option value="government">Government</option>
              <option value="retail">Retail</option>
              <option value="manufacturing">Manufacturing</option>
              <option value="nonprofit">Non-Profit</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div class="field-group">
            <label>Organization Size</label>
            <select v-model="form.org_size" class="field-input">
              <option value="">Select size</option>
              <option value="small">Small (1–50)</option>
              <option value="medium">Medium (51–200)</option>
              <option value="large">Large (201–1000)</option>
              <option value="enterprise">Enterprise (1000+)</option>
            </select>
          </div>
        </div>
        <div class="field-group">
          <label>Brief Description</label>
          <textarea v-model="form.description" placeholder="What does your organization do?" class="field-input" rows="3"></textarea>
        </div>
      </div>

      <!-- Step 2: Admin Account -->
      <div v-if="step === 2" class="step-body">
        <div class="info-box">This account will be the Super Admin of your organization.</div>
        <div class="field-group">
          <label>Username *</label>
          <input v-model="form.username" type="text" placeholder="e.g. john_admin" class="field-input" />
        </div>
        <div class="field-group">
          <label>Email Address *</label>
          <input v-model="form.email" type="email" placeholder="you@company.com" class="field-input" />
        </div>
        <div class="field-group">
          <label>Password *</label>
          <input v-model="form.password" type="password" placeholder="Min 8 characters" class="field-input" />
        </div>
        <div class="field-group">
          <label>Confirm Password *</label>
          <input v-model="form.confirm_password" type="password" placeholder="Re-enter password" class="field-input" />
        </div>
      </div>

      <!-- Step 3: Plan Selection -->
      <div v-if="step === 3" class="step-body">
        <div class="billing-toggle">
          <span :class="{ active: form.billing_cycle === 'monthly' }">Monthly</span>
          <div class="toggle-switch" @click="toggleBilling">
            <div class="toggle-knob" :class="{ annual: form.billing_cycle === 'annual' }"></div>
          </div>
          <span :class="{ active: form.billing_cycle === 'annual' }">Annual <span class="save-badge">Save 20%</span></span>
        </div>

        <div class="plan-options">
          <div
            v-for="p in plans"
            :key="p.key"
            class="plan-option"
            :class="{ selected: form.plan === p.key, popular: p.popular }"
            @click="form.plan = p.key"
          >
            <div class="pop-tag" v-if="p.popular">Popular</div>
            <div class="plan-opt-header">
              <div class="plan-opt-name">{{ p.name }}</div>
              <div class="plan-opt-price">
                ${{ form.billing_cycle === 'monthly' ? p.monthly : p.annualMonthly }}<span>/mo</span>
              </div>
            </div>
            <div class="plan-opt-storage">{{ p.storage }} free storage · ${{ p.overageRate }}/GB extra</div>
            <div class="plan-opt-features">
              <span v-for="f in p.highlights" :key="f" class="feature-chip">{{ f }}</span>
            </div>
          </div>
        </div>

        <div class="summary-box">
          <div class="summary-row">
            <span>Selected plan</span><strong>{{ selectedPlanLabel }}</strong>
          </div>
          <div class="summary-row">
            <span>Billing</span><strong>{{ form.billing_cycle === 'annual' ? 'Annual (20% off)' : 'Monthly' }}</strong>
          </div>
          <div class="summary-row total">
            <span>Total today</span>
            <strong>${{ selectedPlanTotal }}</strong>
          </div>
        </div>
      </div>

      <!-- Error -->
      <div class="error-msg" v-if="error">{{ error }}</div>

      <!-- Navigation -->
      <div class="ob-actions">
        <button class="btn btn-ghost" v-if="step > 1" @click="step--" :disabled="loading">Back</button>
        <div v-else></div>

        <button
          v-if="step < 3"
          class="btn btn-primary"
          @click="nextStep"
          :disabled="loading"
        >
          Next →
        </button>

        <button
          v-if="step === 3"
          class="btn btn-primary"
          @click="submitAndPay"
          :disabled="loading"
        >
          <span v-if="loading">Processing…</span>
          <span v-else>Pay & Create Organization →</span>
        </button>
      </div>

      <div class="ob-footer">
        Already have an account? <a href="/login">Sign in</a> · <a href="/pricing">View pricing</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { createCheckoutSession } from '@/api/index.js'

const route   = useRoute()
const step    = ref(1)
const loading = ref(false)
const error   = ref('')

const stepLabels = ['Organization Details', 'Admin Account', 'Choose Plan & Pay']

const form = ref({
  org_name:         '',
  org_type:         'technology',
  org_size:         '',
  description:      '',
  username:         '',
  email:            '',
  password:         '',
  confirm_password: '',
  plan:             route.query.plan || 'professional',
  billing_cycle:    route.query.billing || 'monthly',
})

const plans = [
  {
    key: 'basic', name: 'Basic', popular: false,
    monthly: 20, annualMonthly: 16, annualTotal: 192,
    storage: '5 GB', overageRate: 5,
    highlights: ['Roles & Permissions', 'User Invitations', 'Up to 20 users'],
  },
  {
    key: 'professional', name: 'Professional', popular: true,
    monthly: 40, annualMonthly: 32, annualTotal: 384,
    storage: '20 GB', overageRate: 4,
    highlights: ['Everything in Basic', 'Screen Recording', 'AI Transcription', 'PDF Export'],
  },
  {
    key: 'premium', name: 'Premium', popular: false,
    monthly: 80, annualMonthly: 64, annualTotal: 768,
    storage: '50 GB', overageRate: 3,
    highlights: ['Everything in Pro', 'Multi-org', 'Audit Logs', 'Priority Support'],
  },
]

const selectedPlan = computed(() => plans.find(p => p.key === form.value.plan))
const selectedPlanLabel = computed(() => selectedPlan.value?.name || '')
const selectedPlanTotal = computed(() => {
  if (!selectedPlan.value) return 0
  return form.value.billing_cycle === 'annual'
    ? selectedPlan.value.annualTotal
    : selectedPlan.value.monthly
})

function toggleBilling() {
  form.value.billing_cycle = form.value.billing_cycle === 'monthly' ? 'annual' : 'monthly'
}

function nextStep() {
  error.value = ''
  if (step.value === 1) {
    if (!form.value.org_name.trim()) { error.value = 'Organization name is required.'; return }
  }
  if (step.value === 2) {
    if (!form.value.username.trim()) { error.value = 'Username is required.'; return }
    if (!form.value.email.trim())    { error.value = 'Email is required.'; return }
    if (form.value.password.length < 8) { error.value = 'Password must be at least 8 characters.'; return }
    if (form.value.password !== form.value.confirm_password) { error.value = 'Passwords do not match.'; return }
  }
  step.value++
}

async function submitAndPay() {
  error.value = ''
  loading.value = true
  try {
    const payload = {
      org_name:      form.value.org_name,
      org_type:      form.value.org_type,
      org_size:      form.value.org_size,
      plan:          form.value.plan,
      billing_cycle: form.value.billing_cycle,
      username:      form.value.username,
      email:         form.value.email,
      password:      form.value.password,
    }
    const { data } = await createCheckoutSession(payload)
    window.location.href = data.checkout_url
  } catch (e) {
    error.value = e.response?.data?.error || 'Something went wrong. Please try again.'
    loading.value = false
  }
}

onMounted(() => {
  if (route.query.cancelled) error.value = 'Payment was cancelled. You can try again below.'
})
</script>

<style scoped>
.onboarding-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 32px 16px; background: var(--bg); }

.onboarding-card { background: var(--surface); border: 1.5px solid var(--border); border-radius: 20px; padding: 40px 36px; max-width: 560px; width: 100%; }

.ob-logo { font-size: 22px; font-weight: 800; color: var(--accent); text-align: center; margin-bottom: 28px; }

/* Step indicator */
.step-indicator { display: flex; align-items: center; justify-content: center; gap: 0; position: relative; margin-bottom: 8px; }
.step-dot { width: 32px; height: 32px; border-radius: 50%; border: 2px solid var(--border); background: var(--surface); display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; color: var(--text-muted); z-index: 1; transition: all .2s; }
.step-dot.active { border-color: var(--accent); color: var(--accent); }
.step-dot.done   { background: var(--accent); border-color: var(--accent); color: #fff; }
.step-dot:not(:last-child)::after { content: ''; display: block; width: 80px; height: 2px; background: var(--border); margin: 0 4px; }
.step-dot.done::after { background: var(--accent); }
.step-line { display: none; }

.step-label { text-align: center; color: var(--text-muted); font-size: 13px; margin-bottom: 28px; }

/* Fields */
.step-body    { display: flex; flex-direction: column; gap: 18px; margin-bottom: 24px; }
.field-row    { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.field-group  { display: flex; flex-direction: column; gap: 6px; }
.field-group label { font-size: 13px; font-weight: 600; }
.field-input  { padding: 10px 14px; border: 1.5px solid var(--border); border-radius: 8px; background: var(--bg); color: var(--text); font-size: 14px; outline: none; transition: border-color .2s; width: 100%; box-sizing: border-box; }
.field-input:focus { border-color: var(--accent); }

.info-box { background: rgba(108,99,255,.07); border: 1px solid rgba(108,99,255,.2); border-radius: 8px; padding: 10px 14px; font-size: 13px; color: var(--accent); }

/* Billing toggle */
.billing-toggle { display: flex; align-items: center; justify-content: center; gap: 12px; font-size: 14px; font-weight: 500; margin-bottom: 20px; }
.billing-toggle span { color: var(--text-muted); transition: color .2s; }
.billing-toggle span.active { color: var(--text); }
.save-badge { background: #10b981; color: #fff; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 20px; margin-left: 4px; }
.toggle-switch { width: 40px; height: 22px; background: var(--border); border-radius: 11px; cursor: pointer; position: relative; }
.toggle-knob   { width: 16px; height: 16px; background: var(--accent); border-radius: 50%; position: absolute; top: 3px; left: 3px; transition: transform .2s; }
.toggle-knob.annual { transform: translateX(18px); }

/* Plan options */
.plan-options { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
.plan-option  { border: 1.5px solid var(--border); border-radius: 12px; padding: 16px; cursor: pointer; position: relative; transition: border-color .2s; }
.plan-option:hover   { border-color: var(--accent); }
.plan-option.selected { border-color: var(--accent); background: rgba(108,99,255,.04); }
.plan-option.popular  { border-color: var(--accent); }
.pop-tag { position: absolute; top: -10px; right: 14px; background: var(--accent); color: #fff; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 10px; }
.plan-opt-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
.plan-opt-name  { font-weight: 700; font-size: 15px; }
.plan-opt-price { font-size: 20px; font-weight: 800; }
.plan-opt-price span { font-size: 13px; font-weight: 400; color: var(--text-muted); }
.plan-opt-storage { font-size: 12px; color: var(--accent); margin-bottom: 10px; }
.plan-opt-features { display: flex; flex-wrap: wrap; gap: 6px; }
.feature-chip { background: var(--bg); border: 1px solid var(--border); border-radius: 20px; font-size: 11px; padding: 2px 8px; color: var(--text-muted); }

/* Summary */
.summary-box  { background: var(--bg); border-radius: 10px; padding: 16px; margin-bottom: 4px; }
.summary-row  { display: flex; justify-content: space-between; font-size: 14px; padding: 5px 0; color: var(--text-muted); }
.summary-row strong { color: var(--text); }
.summary-row.total  { border-top: 1px solid var(--border); margin-top: 8px; padding-top: 12px; font-weight: 700; color: var(--text); font-size: 16px; }
.summary-row.total strong { font-size: 18px; color: var(--accent); }

.error-msg  { color: #ef4444; font-size: 13px; background: rgba(239,68,68,.08); border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; }

/* Actions */
.ob-actions { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 20px; }
.ob-actions .btn { min-width: 120px; }

.ob-footer { text-align: center; font-size: 13px; color: var(--text-muted); }
.ob-footer a { color: var(--accent); text-decoration: none; }
</style>
