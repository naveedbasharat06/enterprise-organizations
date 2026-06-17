<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">Roles</div>
        <div class="page-sub">{{ isSuperAdmin ? 'Manage all roles across organizations' : 'Manage roles for your organization' }}</div>
      </div>
      <button class="btn btn-primary" @click="openCreate">+ New Role</button>
    </div>

    <div class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Role</th><th>Organization</th><th>Permissions</th><th>Created By</th><th>Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="r in roles" :key="r.id">
              <td>
                <div style="font-weight:600;">{{ r.name }}</div>
                <div style="font-size:12px;color:var(--text-muted);">{{ r.description || '' }}</div>
              </td>
              <td>{{ r.organization_name || '— Global —' }}</td>
              <td>
                <div class="perm-chips">
                  <span v-for="p in r.permissions.slice(0,3)" :key="p.id" class="perm-chip">{{ p.name }}</span>
                  <span v-if="r.permissions.length > 3" class="perm-chip more">+{{ r.permissions.length - 3 }} more</span>
                  <span v-if="r.permissions.length === 0" style="color:var(--text-muted);font-size:12px;">None</span>
                </div>
              </td>
              <td style="color:var(--text-muted);">{{ r.created_by_username || '—' }}</td>
              <td>
                <div class="actions">
                  <button v-if="canManage(r)" class="btn btn-ghost btn-sm" @click="openEdit(r)">Edit</button>
                  <button class="btn btn-primary btn-sm" @click="openAssignPerms(r)">Permissions</button>
                  <button v-if="canManage(r)" class="btn btn-danger btn-sm" @click="handleDelete(r)">Delete</button>
                  <span v-if="!canManage(r)" style="font-size:12px;color:var(--text-muted);">View only</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="roles.length === 0" class="empty-state">
          <div class="empty-icon">🎭</div><div>No roles yet. Create your first role.</div>
        </div>
      </div>
    </div>

    <!-- Create / Edit Role Modal -->
    <div v-if="modal.show && (modal.type === 'create' || modal.type === 'edit')" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">{{ modal.type === 'create' ? '🎭 New Role' : '✏️ Edit Role' }}</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="form-group">
          <label>Role Name *</label>
          <input class="form-control" v-model="modal.data.name" placeholder="e.g. Report Viewer" />
        </div>
        <div class="form-group">
          <label>Description</label>
          <div class="desc-row">
            <input class="form-control" v-model="modal.data.description" placeholder="Optional — or generate with AI" />
            <button
              type="button"
              class="btn btn-ghost btn-sm gen-btn"
              :disabled="!modal.data.name || descLoading"
              @click="handleGenerateDescription"
            >{{ descLoading ? '…' : '✨ Generate' }}</button>
          </div>
          <div v-if="descError" class="gen-error">{{ descError }}</div>
        </div>
        <div v-if="isSuperAdmin" class="form-group">
          <label>Organization <span style="font-size:11px;color:var(--text-muted)">(leave blank for global)</span></label>
          <select class="form-control" v-model="modal.data.organization">
            <option :value="null">— Global (all orgs) —</option>
            <option v-for="o in orgs" :key="o.id" :value="o.id">{{ o.name }}</option>
          </select>
        </div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="saveRole" :disabled="modal.loading">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>{{ modal.type === 'create' ? 'Create Role' : 'Save Changes' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Assign Permissions Modal -->
    <div v-if="modal.show && modal.type === 'assignPerms'" class="modal-overlay" @click.self="closeModal">
      <div class="modal" style="max-width:500px;">
        <div class="modal-header">
          <div class="modal-title">🔑 Permissions for "{{ modal.data.name }}"</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div style="margin-bottom:12px;font-size:13px;color:var(--text-muted);">Select permissions to assign to this role:</div>
        <div class="perm-list">
          <label v-for="p in allPermissions" :key="p.id" class="perm-check-item">
            <input type="checkbox" :value="p.id" v-model="modal.selectedPerms" />
            <div>
              <div style="font-weight:600;font-size:13px;">{{ p.name }}</div>
              <div style="font-size:11px;color:var(--text-muted);">{{ p.codename }}</div>
            </div>
          </label>
          <div v-if="allPermissions.length === 0" style="color:var(--text-muted);font-size:13px;padding:8px 0;">
            No permissions available. Create permissions first.
          </div>
        </div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer" style="flex-wrap:wrap;gap:8px;">
          <button class="btn btn-ghost btn-sm" style="margin-right:auto;" :disabled="descLoading" @click="handleAutoDescribeFromPerms">
            {{ descLoading ? '…' : '✨ Auto-generate Description' }}
          </button>
          <button class="btn btn-ghost" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="savePermissions" :disabled="modal.loading">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>Save Permissions</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { generateRoleDescription } from '@/api'

const store          = useStore()
const roles          = computed(() => store.getters['roles/list'])
const allPermissions = computed(() => store.getters['perms/list'])
const orgs           = computed(() => store.getters['orgs/list'])
const isSuperAdmin   = computed(() => store.getters['auth/isSuperAdmin'])
const user           = computed(() => store.getters['auth/user'])

function canManage(r) {
  if (isSuperAdmin.value) return true
  return r.created_by_username === user.value?.username
}

const modal = reactive({ show: false, type: '', data: {}, selectedPerms: [], error: null, loading: false })
function openAssignPerms(r) {
  modal.show = true; modal.type = 'assignPerms'
  modal.data = { id: r.id, name: r.name }
  modal.selectedPerms = r.permissions.map(p => p.id)
  modal.error = null
}
function closeModal() { modal.show = false; modal.error = null }

async function saveRole() {
  modal.error = null
  if (!modal.data.name) { modal.error = 'Role name is required'; return }
  modal.loading = true
  try {
    if (modal.type === 'create') {
      await store.dispatch('roles/create', modal.data)
      store.dispatch('showToast', { message: 'Role created!' })
    } else {
      await store.dispatch('roles/update', modal.data)
      store.dispatch('showToast', { message: 'Role updated!' })
    }
    closeModal()
  } catch (e) {
    modal.error = e.response?.data?.error || e.response?.data?.name?.[0] || 'Failed to save'
  } finally { modal.loading = false }
}

async function savePermissions() {
  modal.loading = true; modal.error = null
  try {
    await store.dispatch('roles/assignPermissions', { id: modal.data.id, permission_ids: modal.selectedPerms })
    store.dispatch('showToast', { message: 'Permissions updated!' })
    closeModal()
  } catch (e) {
    modal.error = e.response?.data?.error || 'Failed to save permissions'
  } finally { modal.loading = false }
}

async function handleDelete(r) {
  if (!confirm(`Delete role "${r.name}"?`)) return
  try {
    await store.dispatch('roles/remove', r.id)
    store.dispatch('showToast', { message: 'Role deleted' })
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Failed to delete', type: 'error' })
  }
}

// ── AI Role Description Generator ────────────────────────────────────────────
const descLoading = ref(false)
const descError   = ref('')

function openCreate() {
  modal.show = true; modal.type = 'create'
  modal.data = { name: '', description: '', organization: null }
  modal.error = null; descError.value = ''
}
function openEdit(r) {
  modal.show = true; modal.type = 'edit'
  modal.data = { id: r.id, name: r.name, description: r.description, organization: r.organization }
  modal.error = null; descError.value = ''
}

async function handleGenerateDescription() {
  if (!modal.data.name) return
  descLoading.value = true
  descError.value   = ''
  try {
    // For edit mode, include current permissions; for create, just use the name
    let permNames = []
    if (modal.type === 'edit') {
      const role = roles.value.find(r => r.id === modal.data.id)
      if (role) permNames = role.permissions.map(p => p.name)
    }
    const { data } = await generateRoleDescription(modal.data.name, permNames)
    if (data.error) { descError.value = data.error; return }
    modal.data.description = data.description
  } catch (e) {
    descError.value = e.response?.data?.error || 'AI service unavailable. Please try again.'
  } finally {
    descLoading.value = false
  }
}

async function handleAutoDescribeFromPerms() {
  if (!modal.data.name) return
  descLoading.value = true
  try {
    const permNames = modal.selectedPerms
      .map(id => allPermissions.value.find(p => p.id === id)?.name)
      .filter(Boolean)
    const { data } = await generateRoleDescription(modal.data.name, permNames)
    if (!data.error && data.description) {
      await store.dispatch('roles/update', { id: modal.data.id, description: data.description })
      store.dispatch('showToast', { message: 'Description auto-generated and saved!' })
    }
  } catch {
    store.dispatch('showToast', { message: 'Could not generate description', type: 'error' })
  } finally {
    descLoading.value = false
  }
}

onMounted(async () => {
  await store.dispatch('roles/fetch')
  await store.dispatch('perms/fetch')
  if (isSuperAdmin.value) store.dispatch('orgs/fetch')
})
</script>

<style scoped>
.perm-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.perm-chip {
  background: rgba(99,102,241,.1); color: var(--accent);
  border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 500;
}
.perm-chip.more { background: rgba(255,255,255,.05); color: var(--text-muted); }
.perm-list { display: flex; flex-direction: column; gap: 8px; max-height: 320px; overflow-y: auto; margin-bottom: 16px; }
.perm-check-item {
  display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px;
  border: 1px solid var(--border); border-radius: 8px; cursor: pointer;
}
.perm-check-item:hover { border-color: var(--accent); }
.perm-check-item input { margin-top: 2px; accent-color: var(--accent); }

.desc-row { display: flex; gap: 8px; align-items: center; }
.desc-row .form-control { flex: 1; }
.gen-btn { white-space: nowrap; }
.gen-error { font-size: 12px; color: var(--danger); margin-top: 6px; }
</style>
