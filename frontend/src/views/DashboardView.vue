<template>
  <div>
    <!-- Super Admin / Admin Dashboard -->
    <template v-if="isAdmin">
      <div class="page-header">
        <div>
          <div class="page-title">Welcome, {{ user.username }} 👋</div>
          <div class="page-sub">{{ isSuperAdmin ? 'Super Admin — Full system control' : 'Admin — Manage your organization' }}</div>
        </div>
      </div>

      <div class="stat-grid" v-if="stats">
        <template v-if="isSuperAdmin">
          <div class="stat-card"><div class="stat-label">Organizations</div><div class="stat-value stat-accent">{{ stats.total_organizations }}</div></div>
          <div class="stat-card"><div class="stat-label">Total Users</div><div class="stat-value stat-green">{{ stats.total_users }}</div></div>
          <div class="stat-card"><div class="stat-label">Admins</div><div class="stat-value stat-warn">{{ stats.total_admins }}</div></div>
          <div class="stat-card"><div class="stat-label">Members</div><div class="stat-value">{{ stats.total_members }}</div></div>
        </template>
        <template v-else>
          <div class="stat-card"><div class="stat-label">My Organization</div><div class="stat-value" style="font-size:18px;margin-top:12px;">{{ stats.organization || 'None' }}</div></div>
          <div class="stat-card"><div class="stat-label">Total Members</div><div class="stat-value stat-green">{{ stats.total_members }}</div></div>
          <div class="stat-card"><div class="stat-label">Admins in Org</div><div class="stat-value stat-warn">{{ stats.admins_in_org }}</div></div>
        </template>
      </div>

      <div class="card">
        <div style="font-size:15px;font-weight:600;margin-bottom:16px;">Quick Actions</div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button v-if="isSuperAdmin" class="btn btn-primary" @click="$router.push('/organizations')">+ New Organization</button>
          <button v-if="isSuperAdmin" class="btn btn-success" @click="$router.push('/users')">+ Create User</button>
          <button class="btn btn-ghost" @click="$router.push('/organizations')">{{ isSuperAdmin ? 'Manage Organizations' : 'View My Organization' }}</button>
          <button class="btn btn-ghost" @click="$router.push('/users')">{{ isSuperAdmin ? 'Manage All Users' : 'Manage My Members' }}</button>
        </div>
      </div>
    </template>

    <!-- Member Dashboard -->
    <template v-else>
      <div class="page-header">
        <div>
          <div class="page-title">Welcome, {{ user.username }} 👋</div>
          <div class="page-sub">Member Dashboard</div>
        </div>
      </div>

      <div style="display:grid;gap:20px;">
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;">
          <div class="card"><div class="stat-label" style="margin-bottom:8px;">Your Role</div><span class="role-badge role-member" style="font-size:14px;padding:6px 14px;">Member</span></div>
          <div class="card"><div class="stat-label" style="margin-bottom:8px;">Organization</div><div style="font-size:18px;font-weight:700;">{{ user.organization_name || 'Not Assigned' }}</div></div>
          <div class="card"><div class="stat-label" style="margin-bottom:8px;">Account Status</div><div style="font-size:18px;font-weight:700;color:var(--accent2);">Active ✓</div></div>
        </div>

        <div class="card">
          <div style="font-size:15px;font-weight:600;margin-bottom:8px;">Your Account Info</div>
          <div style="color:var(--text-muted);font-size:13px;line-height:1.8;">
            <div>👤 Username: <strong style="color:var(--text);">{{ user.username }}</strong></div>
            <div>📧 Email: <strong style="color:var(--text);">{{ user.email }}</strong></div>
            <div>🏢 Organization: <strong style="color:var(--text);">{{ user.organization_name || 'Not Assigned Yet' }}</strong></div>
            <div>📅 Joined: <strong style="color:var(--text);">{{ formatDate(user.date_joined) }}</strong></div>
          </div>
          <div style="margin-top:16px;">
            <button class="btn btn-ghost btn-sm" @click="$router.push('/profile')">Edit Profile →</button>
          </div>
        </div>

        <div class="info-box">ℹ️ <strong>Note:</strong> Your organization is managed by your Admin. Contact your Admin if you need to be added or removed.</div>
      </div>
    </template>

    <!-- Storage Widget (shown to all logged-in users with an org) -->
    <div style="margin-top:20px;" v-if="user.organization">
      <StorageUsageWidget />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import StorageUsageWidget from '@/components/StorageUsageWidget.vue'

const store       = useStore()
const user        = computed(() => store.getters['auth/user'])
const isSuperAdmin = computed(() => store.getters['auth/isSuperAdmin'])
const isAdmin      = computed(() => store.getters['auth/isAdmin'])
const stats        = computed(() => store.state.stats)

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
}

onMounted(() => store.dispatch('fetchStats'))
</script>
