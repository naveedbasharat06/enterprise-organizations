<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">{{ isSuperAdmin ? 'Organizations' : 'My Organization' }}</div>
        <div class="page-sub">{{ isSuperAdmin ? 'Manage all organizations' : 'View and manage your organization members' }}</div>
      </div>
      <button v-if="isSuperAdmin" class="btn btn-primary" @click="openCreate">+ New Organization</button>
    </div>

    <div v-if="!isSuperAdmin" class="info-box">
      ℹ️ You can view and manage members of <strong>{{ user.organization_name }}</strong>.
      Only Super Admin can create or manage other organizations.
    </div>

    <div class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th><th>Description</th><th>Members</th><th>Status</th><th>Recording</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="org in orgs" :key="org.id">
              <td style="font-weight:600;">{{ org.name }}</td>
              <td style="color:var(--text-muted);">{{ org.description || '—' }}</td>
              <td>{{ org.member_count }}</td>
              <td><span class="role-badge" :class="org.is_active ? 'role-admin' : 'role-member'">{{ org.is_active ? 'Active' : 'Inactive' }}</span></td>
              <td>
                <span v-if="isSuperAdmin">
                  <span class="role-badge" :class="org.can_use_recording ? 'role-admin' : 'role-member'">
                    {{ org.can_use_recording ? 'Enabled' : 'Disabled' }}
                  </span>
                </span>
                <span v-else style="color:var(--text-muted);font-size:13px;">
                  {{ org.can_use_recording ? 'Enabled' : 'Disabled' }}
                </span>
              </td>
              <td>
                <div class="actions">
                  <template v-if="isSuperAdmin">
                    <button class="btn btn-ghost btn-sm" @click="openEdit(org)">Edit</button>
                    <button class="btn btn-ghost btn-sm" @click="viewMembers(org)">Members</button>
                    <button class="btn btn-sm" :class="org.can_use_recording ? 'btn-danger' : 'btn-success'" @click="handleToggleRecording(org)">
                      {{ org.can_use_recording ? 'Disable Recording' : 'Enable Recording' }}
                    </button>
                    <button class="btn btn-danger btn-sm" @click="handleDelete(org)">Delete</button>
                  </template>
                  <button v-else class="btn btn-success btn-sm" @click="viewMembers(org)">Manage Members</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="orgs.length === 0" class="empty-state">
          <div class="empty-icon">🏢</div>
          <div>{{ !isSuperAdmin ? 'You are not assigned to any organization yet.' : 'No organizations yet.' }}</div>
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
import { reactive, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { toggleOrgRecording } from '@/api'

const store        = useStore()
const user         = computed(() => store.getters['auth/user'])
const isSuperAdmin = computed(() => store.getters['auth/isSuperAdmin'])
const orgs         = computed(() => store.getters['orgs/list'])

const modal = reactive({ show: false, type: '', data: {}, error: null, loading: false })

function formatRole(r) {
  return { super_admin: 'Super Admin', admin: 'Admin', member: 'Member' }[r] || r
}

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

async function saveOrg() {
  if (!modal.data.name) { modal.error = 'Name is required'; return }
  modal.loading = true; modal.error = null
  try {
    if (modal.type === 'create') {
      await store.dispatch('orgs/create', modal.data)
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
    store.dispatch('showToast', { message: 'Organization deleted' })
    store.dispatch('fetchStats')
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Delete failed', type: 'error' })
  }
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

onMounted(() => store.dispatch('orgs/fetch'))
</script>
