<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">{{ isSuperAdmin ? 'All Users' : 'My Members' }}</div>
        <div class="page-sub">{{ isSuperAdmin ? 'Manage all users across all organizations' : 'Members of ' + (user.organization_name || 'your organization') }}</div>
      </div>
      <button v-if="isSuperAdmin" class="btn btn-primary" @click="openCreate">+ New User</button>
    </div>

    <div v-if="!isSuperAdmin" class="info-box">
      ℹ️ You can <strong>add</strong> or <strong>remove</strong> members from your organization.
      Only Super Admin can promote users to Admin.
    </div>

    <div class="card">
      <div v-if="!isSuperAdmin" style="margin-bottom:16px;">
        <button class="btn btn-success btn-sm" @click="openAddMember">+ Add Member to Organization</button>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>User</th><th>Email</th><th>Role</th><th>Organization</th><th>Joined</th><th>Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td style="font-weight:600;">{{ u.username }}</td>
              <td style="color:var(--text-muted);">{{ u.email }}</td>
              <td><span class="role-badge" :class="'role-'+u.role">{{ formatRole(u.role) }}</span></td>
              <td>{{ u.organization_name || '—' }}</td>
              <td style="color:var(--text-muted);">{{ formatDate(u.date_joined) }}</td>
              <td>
                <div class="actions">
                  <template v-if="isSuperAdmin">
                    <button v-if="u.role === 'member'" class="btn btn-success btn-sm" @click="handleMakeAdmin(u)">Make Admin</button>
                    <button v-if="u.role === 'admin'" class="btn btn-warn btn-sm" @click="handleMakeMember(u)">Demote</button>
                    <button class="btn btn-ghost btn-sm" @click="openEdit(u)">Edit</button>
                    <button class="btn btn-primary btn-sm" @click="openManageRoles(u)">Roles</button>
                    <button class="btn btn-primary btn-sm" @click="openManagePerms(u)">Perms</button>
                    <button v-if="u.id !== user.id" class="btn btn-danger btn-sm" @click="handleDelete(u)">Delete</button>
                  </template>
                  <template v-if="!isSuperAdmin && u.role === 'member' && u.id !== user.id">
                    <button class="btn btn-primary btn-sm" @click="openManageRoles(u)">Roles</button>
                    <button class="btn btn-primary btn-sm" @click="openManagePerms(u)">Perms</button>
                    <button class="btn btn-danger btn-sm" @click="handleRemoveMember(u)">Remove</button>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="users.length === 0" class="empty-state">
          <div class="empty-icon">👥</div><div>No users found</div>
        </div>
      </div>
    </div>

    <!-- Create/Edit User Modal -->
    <div v-if="modal.show && (modal.type === 'create' || modal.type === 'edit')" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">{{ modal.type === 'create' ? '👤 New User' : '✏️ Edit User' }}</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="form-group"><label>Username *</label><input class="form-control" v-model="modal.data.username" /></div>
        <div class="form-group"><label>Email *</label><input class="form-control" type="email" v-model="modal.data.email" /></div>
        <div class="form-group"><label>First Name</label><input class="form-control" v-model="modal.data.first_name" /></div>
        <div class="form-group"><label>Last Name</label><input class="form-control" v-model="modal.data.last_name" /></div>
        <div class="form-group">
          <label>Role</label>
          <select class="form-control" v-model="modal.data.role">
            <option value="member">Member</option>
            <option value="admin">Admin</option>
            <option value="super_admin">Super Admin</option>
          </select>
        </div>
        <div class="form-group">
          <label>Organization</label>
          <select class="form-control" v-model="modal.data.organization">
            <option :value="null">None</option>
            <option v-for="org in orgs" :key="org.id" :value="org.id">{{ org.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>{{ modal.type === 'create' ? 'Password *' : 'New Password (leave blank to keep)' }}</label>
          <input class="form-control" type="password" v-model="modal.data.password" />
        </div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="saveUser" :disabled="modal.loading">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>{{ modal.type === 'create' ? 'Create User' : 'Save Changes' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Add Member Modal (Admin) -->
    <div v-if="modal.show && modal.type === 'addMember'" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">➕ Add Member to Organization</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="info-box">Adding member to: <strong>{{ user.organization_name }}</strong></div>
        <div class="form-group">
          <label>Select User *</label>
          <select class="form-control" v-model="modal.data.user_id">
            <option :value="null">— Select a user —</option>
            <option v-for="u in unassigned" :key="u.id" :value="u.id">{{ u.username }} ({{ u.email }})</option>
          </select>
        </div>
        <div v-if="!unassigned.length" style="color:var(--text-muted);font-size:12px;margin-bottom:10px;">
          No unassigned users available.
        </div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancel</button>
          <button class="btn btn-success" @click="confirmAddMember" :disabled="modal.loading || !modal.data.user_id">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>Add Member</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Manage Roles Modal -->
    <div v-if="modal.show && modal.type === 'manageRoles'" class="modal-overlay" @click.self="closeModal">
      <div class="modal" style="max-width:500px;">
        <div class="modal-header">
          <div class="modal-title">🎭 Roles — {{ modal.data.username }}</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div style="margin-bottom:12px;">
          <div style="font-size:13px;font-weight:600;margin-bottom:8px;">Assigned Roles</div>
          <div v-if="modal.userRoles.length === 0" style="color:var(--text-muted);font-size:13px;">No roles assigned yet.</div>
          <div v-for="ur in modal.userRoles" :key="ur.id" class="assigned-item">
            <span>{{ ur.role_name }}</span>
            <button class="btn btn-danger btn-sm" @click="handleRemoveRole(ur.role_id)">Remove</button>
          </div>
        </div>
        <div class="form-group">
          <label>Assign New Role</label>
          <select class="form-control" v-model="modal.selectedRoleId">
            <option :value="null">— Select a role —</option>
            <option v-for="r in availableRoles" :key="r.id" :value="r.id">{{ r.name }} {{ r.organization_name ? '('+r.organization_name+')' : '(Global)' }}</option>
          </select>
        </div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Close</button>
          <button class="btn btn-primary" @click="handleAssignRole" :disabled="!modal.selectedRoleId || modal.loading">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>Assign Role</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Manage Direct Permissions Modal -->
    <div v-if="modal.show && modal.type === 'managePerms'" class="modal-overlay" @click.self="closeModal">
      <div class="modal" style="max-width:500px;">
        <div class="modal-header">
          <div class="modal-title">🔑 Permissions — {{ modal.data.username }}</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div style="margin-bottom:12px;">
          <div style="font-size:13px;font-weight:600;margin-bottom:8px;">Direct Permissions</div>
          <div v-if="modal.userPerms.length === 0" style="color:var(--text-muted);font-size:13px;">No direct permissions assigned.</div>
          <div v-for="up in modal.userPerms" :key="up.id" class="assigned-item">
            <div>
              <div style="font-weight:600;font-size:13px;">{{ up.permission_name }}</div>
              <div style="font-size:11px;color:var(--text-muted);">{{ up.permission_codename }}</div>
            </div>
            <button class="btn btn-danger btn-sm" @click="handleRemovePermission(up.permission_id)">Remove</button>
          </div>
        </div>
        <div class="form-group">
          <label>Assign New Permission</label>
          <select class="form-control" v-model="modal.selectedPermId">
            <option :value="null">— Select a permission —</option>
            <option v-for="p in availablePerms" :key="p.id" :value="p.id">{{ p.name }} ({{ p.codename }})</option>
          </select>
        </div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Close</button>
          <button class="btn btn-primary" @click="handleAssignPermission" :disabled="!modal.selectedPermId || modal.loading">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>Assign Permission</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { getUserRoles, assignRole, removeRole, getUserDirectPermissions, assignPermissionToUser, removePermissionFromUser } from '@/api'

const store        = useStore()
const user         = computed(() => store.getters['auth/user'])
const isSuperAdmin = computed(() => store.getters['auth/isSuperAdmin'])
const users        = computed(() => store.getters['users/list'])
const unassigned   = computed(() => store.getters['users/unassigned'])
const orgs         = computed(() => store.getters['orgs/list'])
const allRoles     = computed(() => store.getters['roles/list'])
const allPerms     = computed(() => store.getters['perms/list'])

const modal = reactive({
  show: false, type: '', data: {}, error: null, loading: false,
  userRoles: [], userPerms: [],
  selectedRoleId: null, selectedPermId: null,
})

const availableRoles = computed(() =>
  allRoles.value.filter(r => !modal.userRoles.some(ur => ur.role_id === r.id))
)
const availablePerms = computed(() =>
  allPerms.value.filter(p => !modal.userPerms.some(up => up.permission_id === p.id))
)

function formatRole(r) {
  return { super_admin: 'Super Admin', admin: 'Admin', member: 'Member' }[r] || r
}
function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
}

function openCreate() {
  modal.show = true; modal.type = 'create'
  modal.data = { username: '', email: '', first_name: '', last_name: '', role: 'member', organization: null, password: '' }
  modal.error = null
}
function openEdit(u) {
  modal.show = true; modal.type = 'edit'
  modal.data = { ...u, password: '' }; modal.error = null
}
async function openAddMember() {
  await store.dispatch('users/fetchUnassigned')
  modal.show = true; modal.type = 'addMember'
  modal.data = { user_id: null }; modal.error = null
}
function closeModal() { modal.show = false; modal.error = null }

async function saveUser() {
  if (!modal.data.username || !modal.data.email) { modal.error = 'Username and email are required'; return }
  if (modal.type === 'create' && !modal.data.password) { modal.error = 'Password is required'; return }
  modal.loading = true; modal.error = null
  const payload = { ...modal.data }
  if (!payload.password) delete payload.password
  try {
    if (modal.type === 'create') {
      await store.dispatch('users/create', payload)
      store.dispatch('showToast', { message: 'User created!' })
    } else {
      await store.dispatch('users/update', payload)
      store.dispatch('showToast', { message: 'User updated!' })
    }
    closeModal()
    store.dispatch('users/fetch')
    store.dispatch('fetchStats')
  } catch (e) {
    modal.error = e.response?.data?.error || JSON.stringify(e.response?.data) || 'Failed to save'
  } finally { modal.loading = false }
}

async function confirmAddMember() {
  if (!modal.data.user_id) { modal.error = 'Please select a user'; return }
  modal.loading = true; modal.error = null
  try {
    await store.dispatch('orgs/addMember', { orgId: user.value.organization, userId: modal.data.user_id })
    store.dispatch('showToast', { message: 'Member added successfully!' })
    closeModal()
    store.dispatch('users/fetch')
    store.dispatch('fetchStats')
  } catch (e) {
    modal.error = e.response?.data?.error || 'Failed to add member'
  } finally { modal.loading = false }
}

async function handleMakeAdmin(u) {
  try {
    await store.dispatch('users/promoteAdmin', u.id)
    store.dispatch('showToast', { message: `${u.username} is now an Admin` })
    store.dispatch('users/fetch')
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Failed', type: 'error' })
  }
}

async function handleMakeMember(u) {
  try {
    await store.dispatch('users/demoteMember', u.id)
    store.dispatch('showToast', { message: `${u.username} demoted to Member` })
    store.dispatch('users/fetch')
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Failed', type: 'error' })
  }
}

async function handleDelete(u) {
  if (!confirm(`Delete user "${u.username}"?`)) return
  try {
    await store.dispatch('users/remove', u.id)
    store.dispatch('showToast', { message: 'User deleted' })
    store.dispatch('fetchStats')
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Delete failed', type: 'error' })
  }
}

async function handleRemoveMember(u) {
  if (!confirm(`Remove "${u.username}" from the organization?`)) return
  try {
    await store.dispatch('orgs/removeMember', { orgId: user.value.organization, userId: u.id })
    store.dispatch('showToast', { message: `${u.username} removed from organization` })
    store.dispatch('users/fetch')
    store.dispatch('fetchStats')
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Failed', type: 'error' })
  }
}

async function openManageRoles(u) {
  modal.show = true; modal.type = 'manageRoles'
  modal.data = { id: u.id, username: u.username }
  modal.selectedRoleId = null; modal.error = null; modal.userRoles = []
  const { data } = await getUserRoles(u.id)
  modal.userRoles = data
}

async function handleAssignRole() {
  if (!modal.selectedRoleId) return
  modal.loading = true; modal.error = null
  try {
    await assignRole(modal.data.id, modal.selectedRoleId)
    const { data } = await getUserRoles(modal.data.id)
    modal.userRoles = data; modal.selectedRoleId = null
    store.dispatch('showToast', { message: 'Role assigned!' })
  } catch (e) {
    modal.error = e.response?.data?.error || 'Failed to assign role'
  } finally { modal.loading = false }
}

async function handleRemoveRole(roleId) {
  modal.loading = true
  try {
    await removeRole(modal.data.id, roleId)
    const { data } = await getUserRoles(modal.data.id)
    modal.userRoles = data
    store.dispatch('showToast', { message: 'Role removed' })
  } catch (e) {
    modal.error = e.response?.data?.error || 'Failed to remove role'
  } finally { modal.loading = false }
}

async function openManagePerms(u) {
  modal.show = true; modal.type = 'managePerms'
  modal.data = { id: u.id, username: u.username }
  modal.selectedPermId = null; modal.error = null; modal.userPerms = []
  const { data } = await getUserDirectPermissions(u.id)
  modal.userPerms = data
}

async function handleAssignPermission() {
  if (!modal.selectedPermId) return
  modal.loading = true; modal.error = null
  try {
    await assignPermissionToUser(modal.data.id, modal.selectedPermId)
    const { data } = await getUserDirectPermissions(modal.data.id)
    modal.userPerms = data; modal.selectedPermId = null
    store.dispatch('showToast', { message: 'Permission assigned!' })
  } catch (e) {
    modal.error = e.response?.data?.error || 'Failed to assign permission'
  } finally { modal.loading = false }
}

async function handleRemovePermission(permId) {
  modal.loading = true
  try {
    await removePermissionFromUser(modal.data.id, permId)
    const { data } = await getUserDirectPermissions(modal.data.id)
    modal.userPerms = data
    store.dispatch('showToast', { message: 'Permission removed' })
  } catch (e) {
    modal.error = e.response?.data?.error || 'Failed to remove permission'
  } finally { modal.loading = false }
}

onMounted(async () => {
  await store.dispatch('users/fetch')
  await store.dispatch('roles/fetch')
  await store.dispatch('perms/fetch')
  if (isSuperAdmin.value) store.dispatch('orgs/fetch')
})
</script>

<style scoped>
.assigned-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 6px;
}
</style>
