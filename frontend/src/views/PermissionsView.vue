<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">Permissions</div>
        <div class="page-sub">Define permissions that can be assigned to roles and users</div>
      </div>
      <button class="btn btn-primary" @click="openCreate">+ New Permission</button>
    </div>

    <div class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Name</th><th>Codename</th><th>Description</th><th>Organization</th><th>Created By</th><th>Created</th><th>Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="p in permissions" :key="p.id">
              <td style="font-weight:600;">{{ p.name }}</td>
              <td><code style="background:rgba(99,102,241,.1);padding:2px 8px;border-radius:4px;font-size:12px;">{{ p.codename }}</code></td>
              <td style="color:var(--text-muted);">{{ p.description || '—' }}</td>
              <td>
                <span v-if="p.organization_name" class="org-badge">{{ p.organization_name }}</span>
                <span v-else class="global-badge">Global</span>
              </td>
              <td style="color:var(--text-muted);">{{ p.created_by_username || '—' }}</td>
              <td style="color:var(--text-muted);">{{ formatDate(p.created_at) }}</td>
              <td>
                <div class="actions">
                  <button v-if="canManage(p)" class="btn btn-ghost btn-sm" @click="openEdit(p)">Edit</button>
                  <button v-if="canManage(p)" class="btn btn-danger btn-sm" @click="handleDelete(p)">Delete</button>
                  <span v-if="!canManage(p)" style="font-size:12px;color:var(--text-muted);">View only</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="permissions.length === 0" class="empty-state">
          <div class="empty-icon">🔑</div><div>No permissions yet. Create your first one.</div>
        </div>
      </div>
    </div>

    <!-- Create / Edit Modal -->
    <div v-if="modal.show" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">{{ modal.type === 'create' ? '🔑 New Permission' : '✏️ Edit Permission' }}</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="form-group">
          <label>Name *</label>
          <input class="form-control" v-model="modal.data.name" placeholder="e.g. View Reports" />
        </div>
        <div class="form-group">
          <label>Codename * <span style="font-size:11px;color:var(--text-muted)">(unique, no spaces)</span></label>
          <input class="form-control" v-model="modal.data.codename" placeholder="e.g. view_reports" />
        </div>
        <div class="form-group">
          <label>Description</label>
          <input class="form-control" v-model="modal.data.description" placeholder="Optional description" />
        </div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="save" :disabled="modal.loading">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>{{ modal.type === 'create' ? 'Create' : 'Save' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.org-badge {
  background: rgba(99,102,241,.1); color: var(--accent);
  border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 500;
}
.global-badge {
  background: rgba(255,255,255,.06); color: var(--text-muted);
  border-radius: 4px; padding: 2px 8px; font-size: 11px;
}
</style>

<script setup>
import { reactive, computed, onMounted } from 'vue'
import { useStore } from 'vuex'

const store = useStore()
const permissions  = computed(() => store.getters['perms/list'])
const isSuperAdmin = computed(() => store.getters['auth/isSuperAdmin'])
const modal = reactive({ show: false, type: 'create', data: {}, error: null, loading: false })

function canManage(p) {
  if (isSuperAdmin.value) return true
  return p.organization !== null
}

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
}

function openCreate() {
  modal.show = true; modal.type = 'create'
  modal.data = { name: '', codename: '', description: '' }; modal.error = null
}
function openEdit(p) {
  modal.show = true; modal.type = 'edit'
  modal.data = { ...p }; modal.error = null
}
function closeModal() { modal.show = false; modal.error = null }

async function save() {
  modal.error = null
  if (!modal.data.name || !modal.data.codename) { modal.error = 'Name and codename are required'; return }
  if (/\s/.test(modal.data.codename)) { modal.error = 'Codename cannot contain spaces'; return }
  modal.loading = true
  try {
    if (modal.type === 'create') {
      await store.dispatch('perms/create', modal.data)
      store.dispatch('showToast', { message: 'Permission created!' })
    } else {
      await store.dispatch('perms/update', modal.data)
      store.dispatch('showToast', { message: 'Permission updated!' })
    }
    closeModal()
  } catch (e) {
    modal.error = e.response?.data?.codename?.[0] || e.response?.data?.error || 'Failed to save'
  } finally { modal.loading = false }
}

async function handleDelete(p) {
  if (!confirm(`Delete permission "${p.name}"?`)) return
  try {
    await store.dispatch('perms/remove', p.id)
    store.dispatch('showToast', { message: 'Permission deleted' })
  } catch (e) {
    store.dispatch('showToast', { message: 'Failed to delete', type: 'error' })
  }
}

onMounted(() => store.dispatch('perms/fetch'))
</script>
