<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">{{ isSuperAdmin ? 'All Users' : 'My Members' }}</div>
        <div class="page-sub">{{ isSuperAdmin ? 'Manage all users across all organizations' : 'Members of ' + (user.organization_name || 'your organization') }}</div>
      </div>
      <div style="display:flex;gap:8px;">
        <button v-if="isAdmin" class="btn btn-ghost btn-sm" @click="openHistory">📋 Offboarding History</button>
        <button v-if="isSuperAdmin" class="btn btn-primary" @click="openInvite">✉️ Invite User</button>
      </div>
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
                    <button v-if="u.id !== user.id" class="btn btn-warning btn-sm" @click="openOffboard(u)">🚪 Offboard</button>
                  </template>
                  <template v-if="!isSuperAdmin && u.role === 'member' && u.id !== user.id">
                    <button class="btn btn-primary btn-sm" @click="openManageRoles(u)">Roles</button>
                    <button class="btn btn-primary btn-sm" @click="openManagePerms(u)">Perms</button>
                    <button class="btn btn-danger btn-sm" @click="handleRemoveMember(u)">Remove</button>
                    <button class="btn btn-warning btn-sm" @click="openOffboard(u)">🚪 Offboard</button>
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

    <!-- Invite User Modal -->
    <div v-if="modal.show && modal.type === 'invite'" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">✉️ Invite User</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="info-box" style="margin-bottom:16px;">
          An invitation email will be sent. The user sets their own username and password via the link.
        </div>
        <div class="form-group"><label>Email *</label><input class="form-control" type="email" v-model="modal.data.email" placeholder="user@example.com" /></div>
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
        <div v-if="modal.success" class="success-msg">{{ modal.success }}</div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="sendInvite" :disabled="modal.loading">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>Send Invitation</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Edit User Modal -->
    <div v-if="modal.show && modal.type === 'edit'" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">✏️ Edit User</div>
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
          <label>New Password <span style="font-size:11px;color:var(--text-muted)">(leave blank to keep current)</span></label>
          <input class="form-control" type="password" v-model="modal.data.password" />
        </div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="saveUser" :disabled="modal.loading">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>Save Changes</span>
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

        <!-- AI Suggester -->
        <div class="suggest-box">
          <div class="suggest-label">✨ AI Role Suggester</div>
          <div class="suggest-row">
            <input
              v-model="jobTitle"
              class="form-control"
              placeholder="Enter job title e.g. Sales Manager"
              @keyup.enter="handleSuggestRoles"
            />
            <button class="btn btn-primary btn-sm" @click="handleSuggestRoles" :disabled="suggestLoading || !jobTitle.trim()">
              {{ suggestLoading ? '…' : 'Suggest' }}
            </button>
          </div>
          <div v-if="suggestReason && suggestions.length > 0" class="suggest-results">
            <div class="suggest-reason">{{ suggestReason }}</div>
            <div class="suggest-chips">
              <span
                v-for="s in suggestions" :key="s"
                class="suggest-chip"
                @click="selectSuggestedRole(s)"
              >+ {{ s }}</span>
            </div>
          </div>
          <div v-if="suggestReason && suggestions.length === 0 && !suggestError" class="suggest-reason" style="margin-top:8px;">
            {{ suggestReason }}
          </div>
          <div v-if="suggestError" class="suggest-error">{{ suggestError }}</div>
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

        <!-- AI Permission Suggester -->
        <div class="suggest-box">
          <div class="suggest-label">🤖 AI Permission Suggester</div>
          <div class="suggest-row">
            <input
              v-model="permJobTitle"
              class="form-control"
              placeholder="Enter job title e.g. Finance Manager"
              @keyup.enter="handleSuggestPermissions"
            />
            <button class="btn btn-primary btn-sm" @click="handleSuggestPermissions" :disabled="permSuggestLoading || !permJobTitle.trim()">
              {{ permSuggestLoading ? '…' : 'Suggest' }}
            </button>
          </div>
          <div v-if="permSuggestions.length > 0" class="suggest-results">
            <div class="suggest-reason">{{ permSuggestReason }}</div>
            <div class="suggest-chips">
              <span
                v-for="s in permSuggestions" :key="s"
                class="suggest-chip"
                @click="selectSuggestedPerm(s)"
              >+ {{ s }}</span>
            </div>
          </div>
          <div v-if="permSuggestReason && permSuggestions.length === 0 && !permSuggestError" class="suggest-reason" style="margin-top:8px;">
            {{ permSuggestReason }}
          </div>
          <div v-if="permSuggestError" class="suggest-error">{{ permSuggestError }}</div>
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

    <!-- Offboarding Modal -->
    <div v-if="offboard.show" class="modal-overlay" @click.self="offboard.show = false">
      <div class="modal" style="max-width:520px;">
        <div class="modal-header">
          <div class="modal-title">🚪 Offboard — {{ offboard.user?.username }}</div>
          <button class="modal-close" @click="offboard.show = false">✕</button>
        </div>

        <div v-if="offboard.loading" style="text-align:center;padding:32px;">
          <div class="spinner" style="margin:0 auto 12px;width:28px;height:28px;border-width:3px;"></div>
          <div style="font-size:13px;color:var(--text-muted);">AI is analyzing access… please wait</div>
        </div>

        <template v-else-if="offboard.preview">
          <!-- AI Summary -->
          <div class="ob-summary">
            <div class="ob-summary-label">🤖 AI Security Summary</div>
            <div class="ob-summary-text">{{ offboard.preview.ai_summary }}</div>
          </div>

          <!-- Checklist -->
          <div class="ob-section">
            <div class="ob-section-title">Roles to Remove ({{ offboard.preview.roles.length }})</div>
            <div v-if="offboard.preview.roles.length === 0" class="ob-empty">No roles assigned</div>
            <div v-for="r in offboard.preview.roles" :key="r.role__id" class="ob-item">
              <span class="ob-check">✓</span> 🎭 {{ r.role__name }}
            </div>
          </div>

          <div class="ob-section">
            <div class="ob-section-title">Direct Permissions to Remove ({{ offboard.preview.permissions.length }})</div>
            <div v-if="offboard.preview.permissions.length === 0" class="ob-empty">No direct permissions assigned</div>
            <div v-for="p in offboard.preview.permissions" :key="p.permission__id" class="ob-item">
              <span class="ob-check">✓</span> 🔑 {{ p.permission__name }}
            </div>
          </div>

          <label class="ob-deactivate-row">
            <input type="checkbox" v-model="offboard.deactivate" />
            <span>Also deactivate account (user will not be able to log in)</span>
          </label>

          <div v-if="offboard.error" class="error-msg">{{ offboard.error }}</div>

          <div class="modal-footer">
            <button class="btn btn-ghost" @click="offboard.show = false">Cancel</button>
            <button class="btn btn-danger" @click="handleExecuteOffboard" :disabled="offboard.executing">
              <span v-if="offboard.executing" class="spinner"></span>
              <span v-else>🚪 Confirm Offboarding</span>
            </button>
          </div>
        </template>

        <!-- Done state -->
        <div v-else-if="offboard.done" class="ob-done">
          <div class="ob-done-icon">✅</div>
          <div class="ob-done-title">Offboarding Complete</div>
          <div class="ob-done-sub">{{ offboard.user?.username }} has been successfully offboarded.</div>
          <div v-if="offboard.result?.roles_removed?.length" style="margin-top:10px;font-size:12px;color:var(--text-muted);">
            Removed {{ offboard.result.roles_removed.length }} role(s) and {{ offboard.result.permissions_removed.length }} permission(s).
          </div>
          <button class="btn btn-ghost btn-sm" style="margin-top:16px;" @click="offboard.show = false">Close</button>
        </div>
      </div>
    </div>

    <!-- Offboarding History Modal -->
    <div v-if="historyModal.show" class="modal-overlay" @click.self="historyModal.show = false">
      <div class="modal" style="max-width:600px;">
        <div class="modal-header">
          <div class="modal-title">📋 Offboarding History</div>
          <button class="modal-close" @click="historyModal.show = false">✕</button>
        </div>
        <div v-if="historyModal.loading" style="text-align:center;padding:24px;"><div class="spinner" style="margin:auto;"></div></div>
        <div v-else-if="historyModal.logs.length === 0" class="empty-state" style="padding:24px;">No offboardings recorded yet.</div>
        <div v-else style="max-height:400px;overflow-y:auto;">
          <div v-for="log in historyModal.logs" :key="log.id" class="ob-log-item">
            <div class="ob-log-top">
              <strong>{{ log.username_snapshot }}</strong>
              <span style="font-size:11px;color:var(--text-muted);">{{ formatDate(log.created_at) }}</span>
            </div>
            <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">by {{ log.offboarded_by_username }}</div>
            <div style="font-size:12px;font-style:italic;color:var(--text-muted);margin-bottom:8px;">{{ log.ai_summary }}</div>
            <div class="ob-log-chips">
              <span v-for="r in log.roles_removed" :key="r" class="ob-chip role">🎭 {{ r }}</span>
              <span v-for="p in log.permissions_removed" :key="p" class="ob-chip perm">🔑 {{ p }}</span>
              <span v-if="log.account_deactivated" class="ob-chip deact">🔒 Deactivated</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="historyModal.show = false">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { inviteUser, getUserRoles, assignRole, removeRole, getUserDirectPermissions, assignPermissionToUser, removePermissionFromUser, suggestRoles, suggestPermissions, offboardPreview, offboardExecute, offboardingHistory } from '@/api'

const store        = useStore()
const user         = computed(() => store.getters['auth/user'])
const isSuperAdmin = computed(() => store.getters['auth/isSuperAdmin'])
const isAdmin      = computed(() => store.getters['auth/isAdmin'])
const users        = computed(() => store.getters['users/list'])
const unassigned   = computed(() => store.getters['users/unassigned'])
const orgs         = computed(() => store.getters['orgs/list'])
const allRoles     = computed(() => store.getters['roles/list'])
const allPerms     = computed(() => store.getters['perms/list'])

const modal = reactive({
  show: false, type: '', data: {}, error: null, success: null, loading: false,
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

function openInvite() {
  modal.show = true; modal.type = 'invite'
  modal.data = { email: '', role: 'member', organization: null }
  modal.error = null; modal.success = null
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
function closeModal() { modal.show = false; modal.error = null; modal.success = null }

async function sendInvite() {
  if (!modal.data.email) { modal.error = 'Email is required'; return }
  modal.loading = true; modal.error = null; modal.success = null
  try {
    await inviteUser(modal.data)
    modal.success = `Invitation sent to ${modal.data.email}`
    store.dispatch('showToast', { message: 'Invitation sent!' })
    modal.data.email = ''
  } catch (e) {
    modal.error = e.response?.data?.error || 'Failed to send invitation'
  } finally { modal.loading = false }
}

async function saveUser() {
  if (!modal.data.username || !modal.data.email) { modal.error = 'Username and email are required'; return }
  modal.loading = true; modal.error = null
  const payload = { ...modal.data }
  if (!payload.password) delete payload.password
  try {
    await store.dispatch('users/update', payload)
    store.dispatch('showToast', { message: 'User updated!' })
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
  jobTitle.value = ''; suggestions.value = []; suggestReason.value = ''; suggestError.value = ''
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
  permJobTitle.value = ''; permSuggestions.value = []; permSuggestReason.value = ''; permSuggestError.value = ''
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

// ── AI Role Suggester ─────────────────────────────────────────────────────
const jobTitle      = ref('')
const suggestions   = ref([])
const suggestReason = ref('')
const suggestLoading = ref(false)
const suggestError  = ref('')

async function handleSuggestRoles() {
  if (!jobTitle.value.trim()) return
  suggestLoading.value = true
  suggestions.value  = []
  suggestReason.value = ''
  suggestError.value  = ''
  try {
    const roleNames = availableRoles.value.map(r => r.name)
    const { data } = await suggestRoles(jobTitle.value.trim(), roleNames)
    if (data.error) { suggestError.value = data.error; return }
    suggestions.value  = data.suggestions || []
    suggestReason.value = data.reason || ''
    if (suggestions.value.length === 0 && !suggestReason.value)
      suggestError.value = 'No matching roles found for this job title.'
  } catch (e) {
    suggestError.value = e.response?.data?.error || 'AI service unavailable. Please try again.'
  } finally {
    suggestLoading.value = false
  }
}

function selectSuggestedRole(roleName) {
  const role = availableRoles.value.find(r => r.name === roleName)
  if (role) modal.selectedRoleId = role.id
}

// ── AI Permission Suggester ───────────────────────────────────────────────────
const permJobTitle       = ref('')
const permSuggestions    = ref([])
const permSuggestReason  = ref('')
const permSuggestLoading = ref(false)
const permSuggestError   = ref('')

async function handleSuggestPermissions() {
  if (!permJobTitle.value.trim()) return
  permSuggestLoading.value = true
  permSuggestions.value    = []
  permSuggestReason.value  = ''
  permSuggestError.value   = ''
  try {
    const permNames = availablePerms.value.map(p => p.name)
    const { data } = await suggestPermissions(permJobTitle.value.trim(), permNames)
    if (data.error) { permSuggestError.value = data.error; return }
    permSuggestions.value   = data.suggestions || []
    permSuggestReason.value = data.reason || ''
    if (permSuggestions.value.length === 0 && !permSuggestReason.value)
      permSuggestError.value = 'No matching permissions found for this job title.'
  } catch (e) {
    permSuggestError.value = e.response?.data?.error || 'AI service unavailable. Please try again.'
  } finally {
    permSuggestLoading.value = false
  }
}

function selectSuggestedPerm(permName) {
  const perm = availablePerms.value.find(p => p.name === permName)
  if (perm) modal.selectedPermId = perm.id
}

// ── Offboarding ───────────────────────────────────────────────────────────────
const offboard = reactive({
  show: false, loading: false, executing: false,
  user: null, preview: null, deactivate: false,
  error: '', done: false, result: null,
})

const historyModal = reactive({ show: false, loading: false, logs: [] })

async function openOffboard(u) {
  offboard.show      = true
  offboard.loading   = true
  offboard.user      = u
  offboard.preview   = null
  offboard.done      = false
  offboard.result    = null
  offboard.deactivate = false
  offboard.error     = ''
  try {
    const { data } = await offboardPreview(u.id)
    offboard.preview = data
  } catch (e) {
    offboard.error = e.response?.data?.error || 'Failed to load preview.'
  } finally {
    offboard.loading = false
  }
}

async function handleExecuteOffboard() {
  offboard.executing = true
  offboard.error     = ''
  try {
    const { data } = await offboardExecute(offboard.user.id, {
      deactivate_account: offboard.deactivate,
      ai_summary: offboard.preview?.ai_summary || '',
    })
    offboard.result = data
    offboard.done   = true
    offboard.preview = null
    store.dispatch('showToast', { message: `${offboard.user.username} offboarded successfully` })
    store.dispatch('users/fetch')
  } catch (e) {
    offboard.error = e.response?.data?.error || 'Offboarding failed.'
  } finally {
    offboard.executing = false
  }
}

async function openHistory() {
  historyModal.show    = true
  historyModal.loading = true
  historyModal.logs    = []
  try {
    const { data } = await offboardingHistory()
    historyModal.logs = data
  } catch { /* silent */ }
  finally { historyModal.loading = false }
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
.success-msg {
  background: rgba(34,197,94,.12); color: #22c55e;
  border: 1px solid rgba(34,197,94,.25); border-radius: 8px;
  padding: 10px 14px; font-size: 13px; margin-bottom: 12px;
}

.suggest-box {
  background: rgba(108,99,255,.06); border: 1.5px solid rgba(108,99,255,.2);
  border-radius: 10px; padding: 14px; margin-bottom: 16px;
}
.suggest-label { font-size: 12px; font-weight: 700; color: var(--accent); margin-bottom: 10px; text-transform: uppercase; letter-spacing: .04em; }
.suggest-row { display: flex; gap: 8px; }
.suggest-row .form-control { flex: 1; }
.suggest-results { margin-top: 10px; }
.suggest-reason { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; font-style: italic; }
.suggest-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.suggest-chip {
  background: var(--accent); color: #fff; font-size: 12px; font-weight: 600;
  padding: 4px 12px; border-radius: 20px; cursor: pointer; transition: opacity .15s;
}
.suggest-chip:hover { opacity: .85; }
.suggest-error { font-size: 12px; color: var(--danger); margin-top: 8px; }

/* ── Offboarding ── */
.ob-summary { background: rgba(108,99,255,.07); border: 1.5px solid rgba(108,99,255,.2); border-radius: 10px; padding: 14px; margin-bottom: 18px; }
.ob-summary-label { font-size: 11px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
.ob-summary-text  { font-size: 13px; color: var(--text-muted); line-height: 1.6; }
.ob-section { margin-bottom: 14px; }
.ob-section-title { font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; }
.ob-item  { display: flex; align-items: center; gap: 8px; padding: 7px 10px; background: var(--surface2); border-radius: 7px; margin-bottom: 4px; font-size: 13px; }
.ob-check { color: var(--danger); font-weight: 700; font-size: 14px; }
.ob-empty { font-size: 12px; color: var(--text-muted); padding: 4px 0; }
.ob-deactivate-row { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--text-muted); margin: 14px 0 6px; cursor: pointer; }
.ob-deactivate-row input { accent-color: var(--danger); width: 15px; height: 15px; }
.ob-done { text-align: center; padding: 28px 16px; }
.ob-done-icon  { font-size: 48px; margin-bottom: 12px; }
.ob-done-title { font-size: 18px; font-weight: 700; font-family: 'Space Grotesk', sans-serif; margin-bottom: 6px; }
.ob-done-sub   { font-size: 13px; color: var(--text-muted); }
.ob-log-item  { border-bottom: 1px solid var(--border); padding: 14px 0; }
.ob-log-item:last-child { border-bottom: none; }
.ob-log-top   { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; font-size: 14px; }
.ob-log-chips { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }
.ob-chip      { font-size: 11px; font-weight: 600; padding: 3px 9px; border-radius: 12px; }
.ob-chip.role  { background: rgba(108,99,255,.12); color: var(--accent); }
.ob-chip.perm  { background: rgba(0,212,170,.1);   color: var(--accent2); }
.ob-chip.deact { background: rgba(255,77,109,.12); color: var(--danger); }
</style>
