<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">{{ isSuperAdmin ? 'Organizations' : 'My Organizations' }}</div>
        <div class="page-sub">
          {{ isSuperAdmin ? 'Manage all organizations' : 'Manage your organizations and switch between them' }}
        </div>
      </div>
      <button v-if="isSuperAdmin || canAddMore" class="btn btn-primary" @click="openCreate">
        + New Organization
      </button>
    </div>

    <!-- Pending Approvals (Super Admin only) -->
    <div v-if="isSuperAdmin && pendingOrgs.length > 0" class="pending-section">
      <div class="pending-header">
        <span class="pending-title">Pending Verification</span>
        <span class="pending-count">{{ pendingOrgs.length }} awaiting approval</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Org Name</th><th>Plan</th><th>Type</th><th>Members</th><th>Signed Up</th><th>Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="org in pendingOrgs" :key="org.id" class="pending-row">
              <td style="font-weight:600;">{{ org.name }}</td>
              <td><span class="plan-badge" :class="`plan-${org.plan}`">{{ capitalize(org.plan) }}</span></td>
              <td style="color:var(--text-muted);">{{ org.org_type || '—' }}</td>
              <td>{{ org.member_count }}</td>
              <td style="color:var(--text-muted);font-size:13px;">{{ formatDate(org.created_at) }}</td>
              <td>
                <div class="actions">
                  <button class="btn btn-success btn-sm" :disabled="approving === org.id" @click="handleApprove(org)">
                    {{ approving === org.id ? 'Approving…' : 'Approve' }}
                  </button>
                  <button class="btn btn-danger btn-sm" :disabled="approving === org.id" @click="handleReject(org)">
                    Reject
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Plan limit banner for non-super-admin -->
    <div v-if="!isSuperAdmin && limits" class="plan-banner">
      <span class="plan-badge" :class="`plan-${limits.plan}`">{{ capitalize(limits.plan) }}</span>
      <span>
        {{ limits.owned_count }} / {{ limits.max_orgs }} organization{{ limits.max_orgs > 1 ? 's' : '' }} used
      </span>
      <span v-if="!canAddMore && limits.plan !== 'premium'" class="upgrade-hint">
        — Upgrade to Premium to create up to 5 organizations
      </span>
    </div>

    <div class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th><th>Description</th><th>Members</th><th>Status</th><th>Verified</th><th>Recording</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="org in orgs" :key="org.id" :class="{ 'active-row': org.id === currentOrgId }">
              <td>
                <span style="font-weight:600;">{{ org.name }}</span>
                <span v-if="org.id === currentOrgId" class="active-org-pill">Active</span>
              </td>
              <td style="color:var(--text-muted);">{{ org.description || '—' }}</td>
              <td>{{ org.member_count }}</td>
              <td>
                <span class="role-badge" :class="org.is_active ? 'role-admin' : 'role-member'">
                  {{ org.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td>
                <span class="role-badge" :class="org.is_verified ? 'role-admin' : 'badge-pending'">
                  {{ org.is_verified ? 'Verified' : 'Pending' }}
                </span>
              </td>
              <td>
                <span class="role-badge" :class="org.can_use_recording ? 'role-admin' : 'role-member'">
                  {{ org.can_use_recording ? 'Enabled' : 'Disabled' }}
                </span>
              </td>
              <td>
                <div class="actions">
                  <!-- Switch org button for multi-org admins -->
                  <button
                    v-if="org.is_owner && org.id !== currentOrgId"
                    class="btn btn-ghost btn-sm"
                    :disabled="switching === org.id"
                    @click="handleSwitch(org)"
                  >
                    {{ switching === org.id ? 'Switching…' : 'Switch' }}
                  </button>

                  <button class="btn btn-ghost btn-sm" @click="openEdit(org)">Edit</button>
                  <button class="btn btn-ghost btn-sm" @click="viewMembers(org)">Members</button>

                  <template v-if="isSuperAdmin">
                    <button
                      class="btn btn-sm"
                      :class="org.can_use_recording ? 'btn-danger' : 'btn-success'"
                      @click="handleToggleRecording(org)"
                    >
                      {{ org.can_use_recording ? 'Disable Recording' : 'Enable Recording' }}
                    </button>
                    <button class="btn btn-danger btn-sm" @click="handleDelete(org)">Delete</button>
                  </template>

                  <!-- Org admins can delete additional (non-primary) orgs -->
                  <button
                    v-else-if="org.is_owner && !org.stripe_subscription_id"
                    class="btn btn-danger btn-sm"
                    @click="handleDelete(org)"
                  >Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="orgs.length === 0" class="empty-state">
          <div class="empty-icon">🏢</div>
          <div>No organizations yet.</div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="modal.show && (modal.type === 'create' || modal.type === 'edit')" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">{{ modal.type === 'create' ? '🏢 New Organization' : '✏️ Edit Organization' }}</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="form-group">
          <label>Organization Name *</label>
          <input class="form-control" v-model="modal.data.name" placeholder="e.g. Acme Corp" />
        </div>
        <div class="form-group">
          <label>Description</label>
          <input class="form-control" v-model="modal.data.description" placeholder="Brief description" />
        </div>
        <div v-if="modal.type === 'edit'" class="form-group">
          <label>Status</label>
          <select class="form-control" v-model="modal.data.is_active">
            <option :value="true">Active</option>
            <option :value="false">Inactive</option>
          </select>
        </div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="saveOrg" :disabled="modal.loading">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>{{ modal.type === 'create' ? 'Create' : 'Save Changes' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- View Members Modal -->
    <div v-if="modal.show && modal.type === 'members'" class="modal-overlay" @click.self="closeModal">
      <div class="modal" style="width:560px;">
        <div class="modal-header">
          <div class="modal-title">👥 {{ modal.data.orgName }} — Members</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Username</th><th>Email</th><th>Role</th></tr></thead>
            <tbody>
              <tr v-for="m in modal.data.members" :key="m.id">
                <td style="font-weight:600;">{{ m.username }}</td>
                <td style="color:var(--text-muted);">{{ m.email }}</td>
                <td><span class="role-badge" :class="'role-'+m.role">{{ formatRole(m.role) }}</span></td>
              </tr>
            </tbody>
          </table>
          <div v-if="!modal.data.members?.length" class="empty-state"><div class="empty-icon">👥</div><div>No members yet</div></div>
        </div>
        <div class="modal-footer"><button class="btn btn-ghost" @click="closeModal">Close</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { toggleOrgRecording, approveOrg, rejectOrg } from '@/api'

const store  = useStore()
const router = useRouter()

const user         = computed(() => store.getters['auth/user'])
const isSuperAdmin = computed(() => store.getters['auth/isSuperAdmin'])
const orgs         = computed(() => store.getters['orgs/list'])
const limits       = computed(() => store.getters['orgs/limits'])
const canAddMore   = computed(() => store.getters['orgs/canAddMore'])
const currentOrgId = computed(() => user.value?.organization)
const pendingOrgs  = computed(() => orgs.value.filter(o => !o.is_verified && o.is_active))

const modal    = reactive({ show: false, type: '', data: {}, error: null, loading: false })
const switching = ref(null)
const approving = ref(null)

function formatDate(dt) {
  return dt ? new Date(dt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'
}

function formatRole(r) {
  return { super_admin: 'Super Admin', admin: 'Admin', member: 'Member' }[r] || r
}
function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : '' }

function openCreate() {
  modal.show = true; modal.type = 'create'
  modal.data = { name: '', description: '' }; modal.error = null
}
function openEdit(org) {
  modal.show = true; modal.type = 'edit'
  modal.data = { ...org }; modal.error = null
}
function closeModal() { modal.show = false }

async function viewMembers(org) {
  const members = await store.dispatch('orgs/getMembers', org.id)
  modal.show = true; modal.type = 'members'
  modal.data = { orgName: org.name, members }
}

async function handleSwitch(org) {
  switching.value = org.id
  try {
    await store.dispatch('orgs/switchOrg', org.id)
    store.dispatch('showToast', { message: `Switched to ${org.name}` })
    router.push('/')
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Switch failed', type: 'error' })
  } finally {
    switching.value = null
  }
}

async function saveOrg() {
  if (!modal.data.name) { modal.error = 'Name is required'; return }
  modal.loading = true; modal.error = null
  try {
    if (modal.type === 'create') {
      await store.dispatch('orgs/create', modal.data)
      await store.dispatch('orgs/fetchLimits')
      store.dispatch('showToast', { message: 'Organization created!' })
    } else {
      await store.dispatch('orgs/update', modal.data)
      store.dispatch('showToast', { message: 'Organization updated!' })
    }
    closeModal()
    store.dispatch('fetchStats')
  } catch (e) {
    modal.error = e.response?.data?.error || 'Failed to save'
  } finally { modal.loading = false }
}

async function handleDelete(org) {
  if (!confirm(`Delete "${org.name}"? This cannot be undone.`)) return
  try {
    await store.dispatch('orgs/remove', org.id)
    await store.dispatch('orgs/fetchLimits')
    store.dispatch('showToast', { message: 'Organization deleted' })
    store.dispatch('fetchStats')
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Delete failed', type: 'error' })
  }
}

async function handleApprove(org) {
  approving.value = org.id
  try {
    await approveOrg(org.id)
    await store.dispatch('orgs/fetch')
    store.dispatch('showToast', { message: `"${org.name}" approved — members can now log in.` })
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Approval failed', type: 'error' })
  } finally { approving.value = null }
}

async function handleReject(org) {
  if (!confirm(`Reject "${org.name}"? Their members will not be able to log in.`)) return
  approving.value = org.id
  try {
    await rejectOrg(org.id)
    await store.dispatch('orgs/fetch')
    store.dispatch('showToast', { message: `"${org.name}" rejected and deactivated.`, type: 'error' })
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Rejection failed', type: 'error' })
  } finally { approving.value = null }
}

async function handleToggleRecording(org) {
  try {
    const { data } = await toggleOrgRecording(org.id)
    org.can_use_recording = data.can_use_recording
    store.dispatch('showToast', { message: data.message })
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Failed to toggle recording', type: 'error' })
  }
}

onMounted(async () => {
  await store.dispatch('orgs/fetch')
  await store.dispatch('orgs/fetchLimits')
})
</script>

<style scoped>
.active-row { background: rgba(108,99,255,.04); }
.active-org-pill {
  display: inline-block; margin-left: 8px; font-size: 10px; font-weight: 700;
  color: #10b981; background: rgba(16,185,129,.1); padding: 2px 7px; border-radius: 10px;
}
.plan-banner {
  display: flex; align-items: center; gap: 10px; margin-bottom: 20px;
  padding: 10px 16px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; font-size: 14px; color: var(--text-muted);
}
.plan-badge {
  font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px;
  text-transform: uppercase; letter-spacing: .05em;
}
.plan-basic        { background: rgba(108,99,255,.12); color: var(--accent); }
.plan-professional { background: rgba(16,185,129,.12); color: #10b981; }
.plan-premium      { background: rgba(245,158,11,.12); color: #f59e0b; }
.upgrade-hint { color: var(--accent); font-weight: 500; }

/* Pending approvals */
.pending-section {
  margin-bottom: 28px; border: 1.5px solid #f59e0b;
  border-radius: 12px; overflow: hidden;
}
.pending-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px; background: rgba(245,158,11,.08);
}
.pending-title { font-size: 14px; font-weight: 700; color: #f59e0b; }
.pending-count {
  font-size: 12px; font-weight: 600; color: #f59e0b;
  background: rgba(245,158,11,.15); padding: 3px 10px; border-radius: 20px;
}
.pending-row { background: rgba(245,158,11,.03); }
.badge-pending {
  display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px;
  font-weight: 700; background: rgba(245,158,11,.15); color: #f59e0b;
}
</style>
