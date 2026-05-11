<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">My Profile</div>
        <div class="page-sub">Your account information</div>
      </div>
    </div>

    <div class="card" style="max-width:500px;">
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
        <div class="user-avatar-lg">{{ user.username[0].toUpperCase() }}</div>
        <div>
          <div style="font-size:20px;font-weight:700;">{{ user.username }}</div>
          <span class="role-badge" :class="'role-'+user.role">{{ formatRole(user.role) }}</span>
        </div>
      </div>

      <div style="display:grid;gap:12px;font-size:14px;">
        <div><span style="color:var(--text-muted);">Email: </span>{{ user.email }}</div>
        <div><span style="color:var(--text-muted);">First Name: </span>{{ user.first_name || '—' }}</div>
        <div><span style="color:var(--text-muted);">Last Name: </span>{{ user.last_name || '—' }}</div>
        <div><span style="color:var(--text-muted);">Organization: </span>{{ user.organization_name || 'Not Assigned' }}</div>
        <div><span style="color:var(--text-muted);">Joined: </span>{{ formatDate(user.date_joined) }}</div>
      </div>

      <div style="margin-top:20px;">
        <button class="btn btn-ghost" @click="modal.show = true">Edit Profile</button>
      </div>
    </div>

    <!-- Edit Profile Modal -->
    <div v-if="modal.show" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">✏️ Edit My Profile</div>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>
        <div class="form-group"><label>First Name</label><input class="form-control" v-model="form.first_name" /></div>
        <div class="form-group"><label>Last Name</label><input class="form-control" v-model="form.last_name" /></div>
        <div class="form-group"><label>Email</label><input class="form-control" type="email" v-model="form.email" /></div>
        <div class="form-group">
          <label>New Password (leave blank to keep current)</label>
          <input class="form-control" type="password" v-model="form.password" placeholder="New password" />
        </div>
        <div v-if="modal.error" class="error-msg">{{ modal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="saveProfile" :disabled="modal.loading">
            <span v-if="modal.loading" class="spinner"></span>
            <span v-else>Save Changes</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { useStore } from 'vuex'
import { updateUser, getMe } from '@/api'

const store = useStore()
const user  = computed(() => store.getters['auth/user'])

const form  = reactive({ first_name: '', last_name: '', email: '', password: '' })
const modal = reactive({ show: false, error: null, loading: false })

function formatRole(r) {
  return { super_admin: 'Super Admin', admin: 'Admin', member: 'Member' }[r] || r
}
function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
}

function closeModal() {
  modal.show = false; modal.error = null
  // Reset form to current user values
  form.first_name = user.value.first_name || ''
  form.last_name  = user.value.last_name  || ''
  form.email      = user.value.email || ''
  form.password   = ''
}

// Pre-fill when opening
function openEdit() {
  form.first_name = user.value.first_name || ''
  form.last_name  = user.value.last_name  || ''
  form.email      = user.value.email || ''
  form.password   = ''
  modal.show = true; modal.error = null
}

// Watch modal.show to pre-fill
import { watch } from 'vue'
watch(() => modal.show, v => { if (v) openEdit() })

async function saveProfile() {
  modal.loading = true; modal.error = null
  const payload = { first_name: form.first_name, last_name: form.last_name, email: form.email }
  if (form.password) payload.password = form.password
  try {
    await updateUser(user.value.id, payload)
    const { data } = await getMe()
    store.dispatch('auth/updateUser', data)
    store.dispatch('showToast', { message: 'Profile updated!' })
    closeModal()
  } catch (e) {
    modal.error = e.response?.data?.error || JSON.stringify(e.response?.data) || 'Failed to update profile'
  } finally { modal.loading = false }
}
</script>

<style scoped>
.user-avatar-lg {
  width: 56px; height: 56px; border-radius: 50%; font-size: 22px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  display: flex; align-items: center; justify-content: center; font-weight: 700;
}
</style>
