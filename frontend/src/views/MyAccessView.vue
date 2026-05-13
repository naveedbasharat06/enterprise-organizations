<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">My Access</div>
        <div class="page-sub">Your assigned roles and permissions</div>
      </div>
    </div>

    <div v-if="loading" class="loading-state">Loading your access details...</div>

    <template v-else>
      <!-- Summary bar -->
      <div class="summary-bar">
        <div class="summary-card">
          <div class="summary-num">{{ roles.length }}</div>
          <div class="summary-label">Assigned Roles</div>
        </div>
        <div class="summary-card">
          <div class="summary-num">{{ totalRolePermissions }}</div>
          <div class="summary-label">Via Roles</div>
        </div>
        <div class="summary-card">
          <div class="summary-num">{{ directPermissions.length }}</div>
          <div class="summary-label">Direct Permissions</div>
        </div>
        <div class="summary-card">
          <div class="summary-num">{{ allUniquePermissions.size }}</div>
          <div class="summary-label">Total Unique Permissions</div>
        </div>
      </div>

      <!-- Assigned Roles -->
      <div class="section-title">Assigned Roles</div>

      <div v-if="roles.length === 0" class="empty-state">
        <div class="empty-icon">🎭</div>
        <div>No roles have been assigned to you yet.</div>
      </div>

      <div class="role-grid">
        <div class="role-card" v-for="r in roles" :key="r.id">
          <div class="role-card-header">
            <div class="role-name">{{ r.role_name }}</div>
            <span class="perm-count-badge">{{ r.permissions.length }} permission{{ r.permissions.length !== 1 ? 's' : '' }}</span>
          </div>
          <div v-if="r.role_description" class="role-desc">{{ r.role_description }}</div>
          <div class="role-meta">Assigned by {{ r.assigned_by_username || 'system' }} · {{ formatDate(r.assigned_at) }}</div>

          <div v-if="r.permissions.length > 0" class="perm-list">
            <div class="perm-list-label">Permissions included:</div>
            <div class="perm-chips">
              <span class="perm-chip" v-for="p in r.permissions" :key="p.id" :title="p.description || p.codename">
                {{ p.name }}
              </span>
            </div>
          </div>
          <div v-else class="no-perms">This role has no permissions assigned yet.</div>
        </div>
      </div>

      <!-- Direct Permissions -->
      <div class="section-title" style="margin-top:32px;">Direct Permissions</div>
      <div class="page-sub" style="margin-bottom:16px;margin-top:-8px;">
        Permissions assigned to you individually, outside of any role.
      </div>

      <div v-if="directPermissions.length === 0" class="empty-state">
        <div class="empty-icon">🔑</div>
        <div>No direct permissions assigned to you.</div>
      </div>

      <div class="card" v-else>
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Permission</th><th>Codename</th><th>Description</th><th>Assigned By</th><th>Assigned On</th></tr>
            </thead>
            <tbody>
              <tr v-for="p in directPermissions" :key="p.id">
                <td style="font-weight:600;">{{ p.permission_name }}</td>
                <td><code class="code-tag">{{ p.permission_codename }}</code></td>
                <td style="color:var(--text-muted);">{{ p.description || '—' }}</td>
                <td style="color:var(--text-muted);">{{ p.assigned_by_username || '—' }}</td>
                <td style="color:var(--text-muted);">{{ formatDate(p.assigned_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getMyRoles, getMyDirectPermissions } from '@/api/index.js'

const roles = ref([])
const directPermissions = ref([])
const loading = ref(true)

const totalRolePermissions = computed(() =>
  roles.value.reduce((sum, r) => sum + r.permissions.length, 0)
)

const allUniquePermissions = computed(() => {
  const set = new Set()
  roles.value.forEach(r => r.permissions.forEach(p => set.add(p.codename)))
  directPermissions.value.forEach(p => set.add(p.permission_codename))
  return set
})

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
}

onMounted(async () => {
  try {
    const [rolesRes, permsRes] = await Promise.all([getMyRoles(), getMyDirectPermissions()])
    roles.value = rolesRes.data
    directPermissions.value = permsRes.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.summary-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
.summary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  text-align: center;
}
.summary-num {
  font-size: 32px;
  font-weight: 700;
  color: var(--accent);
  font-family: 'Space Grotesk', sans-serif;
}
.summary-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}
.role-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
}
.role-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.role-name {
  font-weight: 700;
  font-size: 15px;
}
.perm-count-badge {
  background: rgba(108,99,255,.15);
  color: var(--accent);
  border-radius: 20px;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 600;
}
.role-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.role-meta {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 14px;
}
.perm-list-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.perm-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.perm-chip {
  background: rgba(108,99,255,.1);
  color: var(--accent);
  border-radius: 6px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 500;
}
.no-perms {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}
.code-tag {
  background: rgba(99,102,241,.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.loading-state {
  text-align: center;
  padding: 60px;
  color: var(--text-muted);
}
</style>
