<template>
  <div class="pricing-page">
    <div class="pricing-header">
      <div class="pricing-title">Simple, Transparent Pricing</div>
      <div class="pricing-sub">Choose the plan that fits your organization. Upgrade or cancel anytime.</div>

      <div class="billing-toggle">
        <span :class="{ active: billing === 'monthly' }">Monthly</span>
        <div class="toggle-switch" @click="toggleBilling">
          <div class="toggle-knob" :class="{ annual: billing === 'annual' }"></div>
        </div>
        <span :class="{ active: billing === 'annual' }">
          Annual <span class="save-badge">Save 20%</span>
        </span>
      </div>
    </div>

    <div class="plans-grid">
      <div
        v-for="plan in plans"
        :key="plan.key"
        class="plan-card"
        :class="{ popular: plan.popular, selected: selectedPlan === plan.key }"
        @click="selectPlan(plan.key)"
      >
        <div class="popular-badge" v-if="plan.popular">Most Popular</div>
        <div class="plan-name">{{ plan.name }}</div>
        <div class="plan-price">
          <span class="price-amount">${{ billing === 'monthly' ? plan.monthly : plan.annualMonthly }}</span>
          <span class="price-period">/month</span>
        </div>
        <div class="price-note" v-if="billing === 'annual'">
          Billed ${{ plan.annualTotal }}/year
        </div>
        <div class="price-note" v-else>&nbsp;</div>

        <div class="storage-note">{{ plan.storage }} free storage · ${{ plan.overageRate }}/GB overage</div>

        <ul class="feature-list">
          <li v-for="f in plan.features" :key="f.text" :class="{ included: f.included, excluded: !f.included }">
            <span class="feature-icon">{{ f.included ? '✓' : '✗' }}</span>
            {{ f.text }}
          </li>
        </ul>

        <button
          class="plan-btn"
          :class="{ 'btn-primary': plan.popular, 'btn-ghost': !plan.popular, 'btn-enterprise': plan.key === 'premium' }"
          @click.stop="handleCta(plan)"
        >
          {{ plan.key === 'premium' ? 'Contact Us' : 'Get Started' }}
        </button>
      </div>
    </div>

    <div class="pricing-footer">
      <div class="footer-note">All plans include a 14-day free trial. No credit card required to start.</div>
      <div class="footer-links">
        Already have an account? <a href="/login">Sign in →</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const billing = ref('monthly')
const selectedPlan = ref('')

function toggleBilling() {
  billing.value = billing.value === 'monthly' ? 'annual' : 'monthly'
}

function selectPlan(key) {
  if (key !== 'premium') selectedPlan.value = key
}

function handleCta(plan) {
  if (plan.key === 'premium') {
    window.location.href = 'mailto:sales@rolebase.com?subject=Premium Plan Enquiry'
    return
  }
  router.push({ path: '/onboarding', query: { plan: plan.key, billing: billing.value } })
}

const plans = [
  {
    key: 'basic', name: 'Basic', popular: false,
    monthly: 20, annualMonthly: 16, annualTotal: 192,
    storage: '5 GB', overageRate: 5,
    features: [
      { text: 'Organization dashboard', included: true },
      { text: 'Custom roles & permissions', included: true },
      { text: 'User invitations via email', included: true },
      { text: 'Up to 20 users', included: true },
      { text: 'Password reset via OTP', included: true },
      { text: 'My Access view', included: true },
      { text: 'Screen recording', included: false },
      { text: 'AI transcription', included: false },
      { text: 'PDF export', included: false },
      { text: 'Multiple organizations', included: false },
    ],
  },
  {
    key: 'professional', name: 'Professional', popular: true,
    monthly: 40, annualMonthly: 32, annualTotal: 384,
    storage: '20 GB', overageRate: 4,
    features: [
      { text: 'Everything in Basic', included: true },
      { text: 'Unlimited users', included: true },
      { text: 'Screen recording (browser)', included: true },
      { text: 'File upload (MP4, WebM, MOV…)', included: true },
      { text: 'AI transcription (Groq Whisper)', included: true },
      { text: 'PDF transcript export', included: true },
      { text: '500 MB per file upload', included: true },
      { text: 'Multiple organizations', included: false },
      { text: 'Audit logs', included: false },
    ],
  },
  {
    key: 'premium', name: 'Premium', popular: false,
    monthly: 80, annualMonthly: 64, annualTotal: 768,
    storage: '50 GB', overageRate: 3,
    features: [
      { text: 'Everything in Professional', included: true },
      { text: 'Multiple organizations', included: true },
      { text: 'Audit logs', included: true },
      { text: '2 GB per file upload', included: true },
      { text: 'Custom branding', included: true },
      { text: 'API access', included: true },
      { text: 'Priority support', included: true },
      { text: 'Dedicated account manager', included: true },
    ],
  },
]
</script>

<style scoped>
.pricing-page { max-width: 1100px; margin: 0 auto; padding: 48px 24px; }

.pricing-header { text-align: center; margin-bottom: 48px; }
.pricing-title  { font-size: 36px; font-weight: 800; margin-bottom: 12px; }
.pricing-sub    { color: var(--text-muted); font-size: 16px; margin-bottom: 32px; }

.billing-toggle { display: flex; align-items: center; justify-content: center; gap: 12px; font-size: 15px; font-weight: 500; }
.billing-toggle span { color: var(--text-muted); transition: color .2s; }
.billing-toggle span.active { color: var(--text); }
.save-badge { background: #10b981; color: #fff; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 20px; margin-left: 6px; }

.toggle-switch { width: 44px; height: 24px; background: var(--border); border-radius: 12px; cursor: pointer; position: relative; transition: background .2s; }
.toggle-knob   { width: 18px; height: 18px; background: var(--accent); border-radius: 50%; position: absolute; top: 3px; left: 3px; transition: transform .2s; }
.toggle-knob.annual { transform: translateX(20px); }

.plans-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; }

.plan-card {
  border: 1.5px solid var(--border);
  border-radius: 16px;
  padding: 32px 28px;
  background: var(--surface);
  position: relative;
  cursor: pointer;
  transition: border-color .2s, box-shadow .2s;
}
.plan-card:hover        { border-color: var(--accent); box-shadow: 0 4px 24px rgba(108,99,255,.12); }
.plan-card.popular      { border-color: var(--accent); box-shadow: 0 4px 24px rgba(108,99,255,.18); }
.plan-card.selected     { border-color: var(--accent2); }

.popular-badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--accent); color: #fff; font-size: 11px; font-weight: 700; padding: 3px 14px; border-radius: 20px; white-space: nowrap; }

.plan-name      { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
.plan-price     { display: flex; align-items: baseline; gap: 4px; }
.price-amount   { font-size: 48px; font-weight: 800; }
.price-period   { color: var(--text-muted); font-size: 16px; }
.price-note     { color: var(--text-muted); font-size: 13px; margin-top: 4px; height: 18px; }
.storage-note   { font-size: 12px; color: var(--accent); background: rgba(108,99,255,.08); padding: 4px 10px; border-radius: 8px; margin: 14px 0; display: inline-block; }

.feature-list { list-style: none; padding: 0; margin: 20px 0 28px; display: flex; flex-direction: column; gap: 10px; }
.feature-list li { font-size: 14px; display: flex; align-items: center; gap: 8px; }
.feature-icon   { font-size: 13px; font-weight: 700; width: 18px; text-align: center; }
.included .feature-icon { color: #10b981; }
.excluded       { color: var(--text-muted); }
.excluded .feature-icon { color: var(--text-muted); }

.plan-btn       { width: 100%; padding: 12px; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer; border: none; transition: opacity .2s; }
.plan-btn:hover { opacity: .85; }
.btn-enterprise { background: linear-gradient(135deg, #f59e0b, #ef4444); color: #fff; }

.pricing-footer { text-align: center; margin-top: 48px; color: var(--text-muted); font-size: 14px; }
.pricing-footer a { color: var(--accent); text-decoration: none; }
.footer-links   { margin-top: 8px; }
</style>
