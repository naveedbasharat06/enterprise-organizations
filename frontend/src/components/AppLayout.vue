<template>
  <div class="layout">
    <!-- MOBILE TOP BAR -->
    <div class="mobile-topbar">
      <button class="hamburger" @click="sidebarOpen = !sidebarOpen">
        <span></span><span></span><span></span>
      </button>
      <div class="mobile-logo">⬡ RoleBase</div>
    </div>

    <!-- SIDEBAR OVERLAY (mobile) -->
    <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false"></div>

    <!-- SIDEBAR -->
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-logo">⬡ RoleBase</div>

      <div class="sidebar-user">
        <div class="user-avatar">{{ user.username[0].toUpperCase() }}</div>
        <div>
          <div class="user-name">{{ user.username }}</div>
          <span class="role-badge" :class="'role-' + user.role">{{ formatRole(user.role) }}</span>
        </div>
      </div>

      <!-- Org Switcher (shown when user owns multiple orgs) -->
      <div v-if="ownedOrgs.length > 1 || canAddMore" class="org-switcher">
        <div class="org-switcher-label">Organization</div>
        <div class="org-switcher-current" @click="toggleSwitcher">
          <span class="org-dot"></span>
          <span class="org-name-text">{{ user.organization_name || 'No Org' }}</span>
          <span class="org-chevron">{{ switcherOpen ? '▲' : '▼' }}</span>
        </div>
        <div v-if="switcherOpen" class="org-dropdown">
          <div
            v-for="org in ownedOrgs"
            :key="org.id"
            class="org-dropdown-item"
            :class="{ active: org.id === user.organization }"
            @click="handleSwitchOrg(org)"
          >
            <span class="org-dot" :class="{ active: org.id === user.organization }"></span>
            <span>{{ org.name }}</span>
            <span v-if="org.id === user.organization" class="org-active-badge">Active</span>
          </div>
          <div v-if="canAddMore" class="org-dropdown-add" @click="goToNewOrg">
            + New Organization
          </div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" custom v-slot="{ navigate, isExactActive }">
          <div class="nav-item" :class="{ active: isExactActive }" @click="navigate(); sidebarOpen = false">
            <span class="nav-icon">📊</span> Dashboard
          </div>
        </router-link>

        <router-link v-if="isAdmin" to="/organizations" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate(); sidebarOpen = false">
            <span class="nav-icon">🏢</span>
            {{ isSuperAdmin ? 'Organizations' : 'My Organization' }}
          </div>
        </router-link>

        <router-link v-if="isAdmin" to="/users" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate(); sidebarOpen = false">
            <span class="nav-icon">👥</span>
            {{ isSuperAdmin ? 'All Users' : 'My Members' }}
          </div>
        </router-link>

        <router-link v-if="isAdmin" to="/roles" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate(); sidebarOpen = false">
            <span class="nav-icon">🎭</span> Roles
          </div>
        </router-link>

        <router-link v-if="isAdmin" to="/permissions" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate(); sidebarOpen = false">
            <span class="nav-icon">🔑</span> Permissions
          </div>
        </router-link>

        <router-link to="/my-access" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate(); sidebarOpen = false">
            <span class="nav-icon">🛡️</span> My Access
          </div>
        </router-link>

        <router-link v-if="canRecord" to="/recording" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate(); sidebarOpen = false">
            <span class="nav-icon">🎬</span> Recording
          </div>
        </router-link>

        <router-link to="/profile" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate(); sidebarOpen = false">
            <span class="nav-icon">👤</span> My Profile
          </div>
        </router-link>

      </nav>

      <div class="sidebar-footer">
        <button class="btn btn-ghost btn-full btn-sm" @click="handleLogout">Sign Out</button>
      </div>
    </aside>

    <!-- MAIN CONTENT -->
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store  = useStore()
const router = useRouter()

const user         = computed(() => store.getters['auth/user'])
const isSuperAdmin = computed(() => store.getters['auth/isSuperAdmin'])
const isAdmin      = computed(() => store.getters['auth/isAdmin'])
const ownedOrgs    = computed(() => store.getters['orgs/ownedOrgs'])
const canAddMore   = computed(() => store.getters['orgs/canAddMore'])
const canRecord    = computed(() => {
  if (!user.value) return false
  if (isSuperAdmin.value) return true
  return user.value.org_recording_enabled === true
})

const switcherOpen = ref(false)
const sidebarOpen  = ref(false)

function toggleSwitcher() { switcherOpen.value = !switcherOpen.value }

async function handleSwitchOrg(org) {
  switcherOpen.value = false
  if (org.id === user.value.organization) return
  await store.dispatch('orgs/switchOrg', org.id)
  store.dispatch('fetchStats')
  router.push('/')
}

function goToNewOrg() {
  switcherOpen.value = false
  router.push('/organizations')
}

function formatRole(r) {
  return { super_admin: 'Super Admin', admin: 'Admin', member: 'Member' }[r] || r
}

async function handleLogout() {
  await store.dispatch('auth/logout')
  router.push('/login')
}

onMounted(() => {
  if (isAdmin.value) {
    store.dispatch('orgs/fetch')
    store.dispatch('orgs/fetchLimits')
  }
})
</script>

<style scoped>
/* ── LAYOUT ── */
.layout { display: flex; min-height: 100vh; }

/* ── MOBILE TOP BAR ── */
.mobile-topbar {
  display: none;
  position: fixed; top: 0; left: 0; right: 0; height: 56px; z-index: 200;
  background: var(--surface); border-bottom: 1px solid var(--border);
  align-items: center; padding: 0 16px; gap: 14px;
}
.mobile-logo {
  font-family: 'Space Grotesk', sans-serif; font-size: 18px;
  font-weight: 700; color: var(--accent);
}
.hamburger {
  background: none; border: none; cursor: pointer;
  display: flex; flex-direction: column; gap: 5px; padding: 4px;
}
.hamburger span {
  display: block; width: 22px; height: 2px;
  background: var(--text); border-radius: 2px; transition: all .2s;
}

/* ── SIDEBAR OVERLAY ── */
.sidebar-overlay {
  display: none;
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  backdrop-filter: blur(2px); z-index: 150;
}

/* ── SIDEBAR ── */
.sidebar {
  width: 240px; background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; position: fixed; height: 100vh; z-index: 160;
  transition: transform .25s ease;
}
.sidebar-logo {
  padding: 24px 20px 20px; font-family: 'Space Grotesk', sans-serif;
  font-size: 20px; font-weight: 700; color: var(--accent); border-bottom: 1px solid var(--border);
}
.sidebar-user {
  padding: 16px 20px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 10px;
}
.user-avatar {
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px;
}
.user-name { font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ── ORG SWITCHER ── */
.org-switcher { padding: 10px 14px; border-bottom: 1px solid var(--border); position: relative; }
.org-switcher-label { font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 6px; }
.org-switcher-current {
  display: flex; align-items: center; gap: 8px; padding: 6px 10px;
  border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 500;
  background: rgba(108,99,255,.08); border: 1px solid var(--border); transition: background .2s;
}
.org-switcher-current:hover { background: rgba(108,99,255,.16); }
.org-name-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.org-chevron { font-size: 10px; color: var(--text-muted); }
.org-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--border); flex-shrink: 0; }
.org-dot.active { background: #10b981; }
.org-dropdown {
  position: absolute; left: 14px; right: 14px; top: calc(100% - 6px);
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,.18); z-index: 50; overflow: hidden;
}
.org-dropdown-item { display: flex; align-items: center; gap: 8px; padding: 10px 14px; font-size: 13px; cursor: pointer; transition: background .15s; }
.org-dropdown-item:hover { background: rgba(108,99,255,.08); }
.org-dropdown-item.active { color: var(--accent); font-weight: 600; }
.org-active-badge { margin-left: auto; font-size: 10px; font-weight: 700; color: #10b981; background: rgba(16,185,129,.1); padding: 2px 7px; border-radius: 10px; }
.org-dropdown-add { padding: 10px 14px; font-size: 13px; font-weight: 600; color: var(--accent); cursor: pointer; border-top: 1px solid var(--border); transition: background .15s; }
.org-dropdown-add:hover { background: rgba(108,99,255,.08); }

/* ── NAV ── */
.sidebar-nav { flex: 1; padding: 12px; overflow-y: auto; }
.nav-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  border-radius: 8px; cursor: pointer; font-size: 14px; color: var(--text-muted);
  transition: all .2s; margin-bottom: 2px;
}
.nav-item:hover, .nav-item.active { background: rgba(108,99,255,.12); color: var(--text); }
.nav-item.active { color: var(--accent); font-weight: 500; }
.nav-icon { font-size: 16px; width: 20px; text-align: center; }
.nav-divider { height: 1px; background: var(--border); margin: 8px 12px; }
.sidebar-footer { padding: 16px; border-top: 1px solid var(--border); }

/* ── MAIN ── */
.main { margin-left: 240px; flex: 1; padding: 32px; }

/* ── MOBILE RESPONSIVE ── */
@media (max-width: 768px) {
  .mobile-topbar  { display: flex; }
  .sidebar-overlay { display: block; }

  .sidebar {
    transform: translateX(-100%);
    top: 0;
  }
  .sidebar.open { transform: translateX(0); }

  /* Hide desktop logo in sidebar on mobile — topbar has it */
  .sidebar-logo { display: none; }

  .main {
    margin-left: 0;
    padding: 16px;
    padding-top: 72px; /* clear fixed topbar */
  }
}
</style>
