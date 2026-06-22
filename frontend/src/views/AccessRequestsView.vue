<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">📋 Access Requests</div>
        <div class="page-sub">{{ isAdmin ? 'Review and manage access requests from your members' : 'Request roles or permissions and track your submissions' }}</div>
      </div>
    </div>

    <!-- TABS -->
    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'submit' }" @click="tab = 'submit'">Submit Request</button>
      <button class="tab" :class="{ active: tab === 'mine' }"   @click="tab = 'mine'; loadRequests()">My Requests</button>
      <button v-if="isAdmin" class="tab" :class="{ active: tab === 'pending' }" @click="tab = 'pending'; loadRequests()">
        Pending Review
        <span v-if="pendingCount > 0" class="badge">{{ pendingCount }}</span>
      </button>
    </div>

    <!-- SUBMIT REQUEST TAB -->
    <div v-if="tab === 'submit'" class="card">
      <div class="form-group">
        <label>Request Type</label>
        <div class="type-row">
          <button class="type-btn" :class="{ active: form.request_type === 'role' }"       @click="form.request_type = 'role'; form.role = null; form.permission = null">🎭 Role</button>
          <button class="type-btn" :class="{ active: form.request_type === 'permission' }" @click="form.request_type = 'permission'; form.role = null; form.permission = null">🔑 Permission</button>
        </div>
      </div>

      <div v-if="form.request_type === 'role'" class="form-group">
        <label>Select Role to Request *</label>
        <select class="form-control" v-model="form.role">
          <option :value="null">— Choose a role —</option>
          <option v-for="r in availableRoles" :key="r.id" :value="r.id">{{ r.name }} {{ r.organization_name ? '('+r.organization_name+')' : '(Global)' }}</option>
        </select>
      </div>

      <div v-if="form.request_type === 'permission'" class="form-group">
        <label>Select Permission to Request *</label>
        <select class="form-control" v-model="form.permission">
          <option :value="null">— Choose a permission —</option>
          <option v-for="p in allPerms" :key="p.id" :value="p.id">{{ p.name }} ({{ p.codename }})</option>
        </select>
      </div>

      <div class="form-group">
        <label>Justification *</label>
        <textarea
          class="form-control"
          v-model="form.justification"
          rows="4"
          placeholder="Explain clearly why you need this access and how you will use it..."
          style="resize:vertical;"
        ></textarea>
        <div class="field-hint">Be specific — AI reviews your justification automatically.</div>
      </div>

      <div v-if="submitError" class="error-msg">{{ submitError }}</div>

      <div v-if="submitResult" class="result-card" :class="submitResult.ai_verdict">
        <div class="result-header">
          <span class="verdict-badge" :class="submitResult.ai_verdict">{{ verdictLabel(submitResult.ai_verdict) }}</span>
          <span class="result-status">Status: <strong>{{ submitResult.status }}</strong></span>
        </div>
        <div class="result-reason">🤖 {{ submitResult.ai_reason }}</div>
        <div v-if="submitResult.status === 'approved'" class="result-granted">
          ✅ Access has been automatically granted to your account.
        </div>
        <div v-else-if="submitResult.ai_verdict === 'needs_review'" class="result-pending">
          ⏳ Your request is pending admin review.
        </div>
      </div>

      <button class="btn btn-primary" @click="handleSubmit" :disabled="submitting || !canSubmit">
        <span v-if="submitting" class="spinner"></span>
        <span v-else>Submit Request</span>
      </button>
    </div>

    <!-- MY REQUESTS TAB -->
    <div v-if="tab === 'mine'" class="card">
      <div v-if="loading" class="empty-state"><div class="spinner"></div></div>
      <div v-else-if="myRequests.length === 0" class="empty-state">
        <div class="empty-icon">📋</div>
        <div>No requests submitted yet.</div>
      </div>
      <div v-else class="request-list">
        <div v-for="r in myRequests" :key="r.id" class="request-item">
          <div class="request-top">
            <div class="request-target">
              <span class="req-type-badge">{{ r.request_type === 'role' ? '🎭' : '🔑' }}</span>
              <strong>{{ r.role_name || r.permission_name }}</strong>
            </div>
            <span class="status-badge" :class="r.status">{{ r.status }}</span>
          </div>
          <div class="request-justification">"{{ r.justification }}"</div>
          <div class="request-meta">
            <span class="verdict-badge sm" :class="r.ai_verdict">{{ verdictLabel(r.ai_verdict) }}</span>
            <span class="meta-reason">{{ r.ai_reason }}</span>
          </div>
          <div v-if="r.reviewed_by_username" class="request-reviewed">
            Reviewed by <strong>{{ r.reviewed_by_username }}</strong>
          </div>
          <div class="request-date">{{ formatDate(r.created_at) }}</div>
        </div>
      </div>
    </div>

    <!-- PENDING REVIEW TAB (admin) -->
    <div v-if="tab === 'pending' && isAdmin" class="card">
      <div v-if="loading" class="empty-state"><div class="spinner"></div></div>
      <div v-else-if="pendingRequests.length === 0" class="empty-state">
        <div class="empty-icon">✅</div>
        <div>No pending requests — all caught up!</div>
      </div>
      <div v-else class="request-list">
        <div v-for="r in pendingRequests" :key="r.id" class="request-item">
          <div class="request-top">
            <div class="request-target">
              <span class="req-type-badge">{{ r.request_type === 'role' ? '🎭' : '🔑' }}</span>
              <strong>{{ r.role_name || r.permission_name }}</strong>
              <span class="by-user">by <strong>{{ r.username }}</strong> ({{ r.user_role }})</span>
            </div>
            <span class="status-badge" :class="r.status">{{ r.status }}</span>
          </div>
          <div class="request-justification">"{{ r.justification }}"</div>
          <div class="request-meta">
            <span class="verdict-badge sm" :class="r.ai_verdict">{{ verdictLabel(r.ai_verdict) }}</span>
            <span class="meta-reason">{{ r.ai_reason }}</span>
          </div>
          <div class="request-date">{{ formatDate(r.created_at) }}</div>
          <div v-if="r.status === 'pending'" class="request-actions">
            <button class="btn btn-success btn-sm" :disabled="actionLoading === r.id" @click="handleApprove(r)">
              {{ actionLoading === r.id ? '…' : '✅ Approve' }}
            </button>
            <button class="btn btn-danger btn-sm"  :disabled="actionLoading === r.id" @click="handleReject(r)">
              {{ actionLoading === r.id ? '…' : '❌ Reject' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { getAccessRequests, createAccessRequest, approveAccessRequest, rejectAccessRequest } from '@/api'

const store   = useStore()
const user    = computed(() => store.getters['auth/user'])
const isAdmin = computed(() => store.getters['auth/isAdmin'])
const allRoles = computed(() => store.getters['roles/list'])
const allPerms = computed(() => store.getters['perms/list'])

const tab          = ref('submit')
const loading      = ref(false)
const submitting   = ref(false)
const actionLoading = ref(null)
const submitError  = ref('')
const submitResult = ref(null)
const allRequests  = ref([])

const form = ref({ request_type: 'role', role: null, permission: null, justification: '' })

const myRequests      = computed(() => allRequests.value.filter(r => r.username === user.value?.username))
const pendingRequests = computed(() => allRequests.value.filter(r => r.status === 'pending'))
const pendingCount    = computed(() => pendingRequests.value.length)

const availableRoles = computed(() => allRoles.value)

const canSubmit = computed(() => {
  if (!form.value.justification.trim()) return false
  if (form.value.request_type === 'role')       return !!form.value.role
  if (form.value.request_type === 'permission') return !!form.value.permission
  return false
})

function verdictLabel(v) {
  return { auto_approve: '🤖 Auto Approved', needs_review: '👁 Needs Review', deny: '🚫 Denied' }[v] || v || '—'
}

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'
}

async function loadRequests() {
  loading.value = true
  try {
    const { data } = await getAccessRequests()
    allRequests.value = data
  } catch { /* silent */ }
  finally { loading.value = false }
}

async function handleSubmit() {
  submitError.value  = ''
  submitResult.value = null
  submitting.value   = true
  try {
    const payload = {
      request_type:  form.value.request_type,
      justification: form.value.justification.trim(),
      role:          form.value.request_type === 'role'       ? form.value.role       : null,
      permission:    form.value.request_type === 'permission' ? form.value.permission : null,
    }
    const { data } = await createAccessRequest(payload)
    submitResult.value = data
    form.value = { request_type: 'role', role: null, permission: null, justification: '' }
    store.dispatch('showToast', { message: 'Request submitted!' })
    await loadRequests()
  } catch (e) {
    submitError.value = e.response?.data?.error || 'Failed to submit request.'
  } finally { submitting.value = false }
}

async function handleApprove(r) {
  actionLoading.value = r.id
  try {
    await approveAccessRequest(r.id)
    store.dispatch('showToast', { message: `Request approved for ${r.username}` })
    await loadRequests()
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Failed', type: 'error' })
  } finally { actionLoading.value = null }
}

async function handleReject(r) {
  actionLoading.value = r.id
  try {
    await rejectAccessRequest(r.id)
    store.dispatch('showToast', { message: `Request rejected for ${r.username}` })
    await loadRequests()
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Failed', type: 'error' })
  } finally { actionLoading.value = null }
}

onMounted(async () => {
  await store.dispatch('roles/fetch')
  await store.dispatch('perms/fetch')
  await loadRequests()
})
</script>

<style scoped>
/* Tabs */
.tabs { display: flex; gap: 4px; margin-bottom: 20px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 4px; width: fit-content; }
.tab  { padding: 8px 18px; border-radius: 7px; border: none; background: none; color: var(--text-muted); font-size: 13px; font-weight: 500; cursor: pointer; font-family: inherit; display: flex; align-items: center; gap: 6px; transition: all .15s; }
.tab.active { background: var(--accent); color: #fff; }
.badge { background: var(--danger); color: #fff; border-radius: 10px; padding: 1px 7px; font-size: 11px; font-weight: 700; }

/* Submit form extras */
.type-row { display: flex; gap: 8px; }
.type-btn { flex: 1; padding: 10px; border: 1.5px solid var(--border); border-radius: 8px; background: var(--surface2); color: var(--text-muted); font-size: 13px; font-weight: 600; cursor: pointer; font-family: inherit; transition: all .15s; }
.type-btn.active { border-color: var(--accent); color: var(--accent); background: rgba(108,99,255,.08); }
.field-hint { font-size: 11px; color: var(--text-muted); margin-top: 5px; }

/* AI result card */
.result-card { border-radius: 10px; padding: 16px; margin-bottom: 16px; border: 1.5px solid var(--border); }
.result-card.auto_approve { border-color: rgba(0,212,170,.4); background: rgba(0,212,170,.06); }
.result-card.needs_review { border-color: rgba(255,179,71,.4); background: rgba(255,179,71,.06); }
.result-card.deny         { border-color: rgba(255,77,109,.4); background: rgba(255,77,109,.06); }
.result-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.result-status { font-size: 13px; color: var(--text-muted); }
.result-reason  { font-size: 13px; color: var(--text-muted); font-style: italic; margin-bottom: 8px; }
.result-granted { font-size: 13px; color: var(--accent2); font-weight: 600; }
.result-pending { font-size: 13px; color: var(--warn); }

/* Verdict badges */
.verdict-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
.verdict-badge.auto_approve { background: rgba(0,212,170,.15); color: var(--accent2); }
.verdict-badge.needs_review { background: rgba(255,179,71,.15); color: var(--warn); }
.verdict-badge.deny         { background: rgba(255,77,109,.15); color: var(--danger); }
.verdict-badge.sm { font-size: 10px; padding: 2px 7px; }

/* Status badges */
.status-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }
.status-badge.pending  { background: rgba(255,179,71,.15);  color: var(--warn); }
.status-badge.approved { background: rgba(0,212,170,.15);   color: var(--accent2); }
.status-badge.rejected { background: rgba(255,77,109,.15);  color: var(--danger); }

/* Request list */
.request-list { display: flex; flex-direction: column; gap: 12px; }
.request-item { border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
.request-top  { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 6px; }
.request-target { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.req-type-badge { font-size: 16px; }
.by-user { font-size: 12px; color: var(--text-muted); margin-left: 4px; }
.request-justification { font-size: 13px; color: var(--text-muted); font-style: italic; margin-bottom: 10px; padding: 8px 12px; background: var(--surface2); border-radius: 6px; }
.request-meta   { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
.meta-reason    { font-size: 12px; color: var(--text-muted); font-style: italic; }
.request-reviewed { font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.request-date   { font-size: 11px; color: var(--text-muted); }
.request-actions { display: flex; gap: 8px; margin-top: 10px; }

@media (max-width: 768px) {
  .tabs { width: 100%; flex-wrap: wrap; }
  .tab  { flex: 1; justify-content: center; }
  .type-row { flex-direction: column; }
}
</style>
