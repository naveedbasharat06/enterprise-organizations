<template>
  <div class="layout">
    <!-- SIDEBAR -->
    <aside class="sidebar">
      <div class="sidebar-logo">⬡ RoleBase</div>

      <div class="sidebar-user">
        <div class="user-avatar">{{ user.username[0].toUpperCase() }}</div>
        <div>
          <div class="user-name">{{ user.username }}</div>
          <span class="role-badge" :class="'role-' + user.role">{{ formatRole(user.role) }}</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate">
            <span class="nav-icon">📊</span> Dashboard
          </div>
        </router-link>

        <router-link v-if="isAdmin" to="/organizations" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate">
            <span class="nav-icon">🏢</span>
            {{ isSuperAdmin ? 'Organizations' : 'My Organization' }}
          </div>
        </router-link>

        <router-link v-if="isAdmin" to="/users" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate">
            <span class="nav-icon">👥</span>
            {{ isSuperAdmin ? 'All Users' : 'My Members' }}
          </div>
        </router-link>

        <router-link v-if="isAdmin" to="/roles" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate">
            <span class="nav-icon">🎭</span> Roles
          </div>
        </router-link>

        <router-link v-if="isAdmin" to="/permissions" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate">
            <span class="nav-icon">🔑</span> Permissions
          </div>
        </router-link>

        <router-link to="/my-access" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate">
            <span class="nav-icon">🛡️</span> My Access
          </div>
        </router-link>

        <router-link to="/profile" custom v-slot="{ navigate, isActive }">
          <div class="nav-item" :class="{ active: isActive }" @click="navigate">
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
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store  = useStore()
const router = useRouter()

const user        = computed(() => store.getters['auth/user'])
const isSuperAdmin = computed(() => store.getters['auth/isSuperAdmin'])
const isAdmin      = computed(() => store.getters['auth/isAdmin'])

function formatRole(r) {
  return { super_admin: 'Super Admin', admin: 'Admin', member: 'Member' }[r] || r
}

async function handleLogout() {
  await store.dispatch('auth/logout')
  router.push('/login')
}
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; }
.sidebar {
  width: 240px; background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; position: fixed; height: 100vh; z-index: 10;
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
.sidebar-nav { flex: 1; padding: 12px; overflow-y: auto; }
.nav-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  border-radius: 8px; cursor: pointer; font-size: 14px; color: var(--text-muted);
  transition: all .2s; margin-bottom: 2px;
}
.nav-item:hover, .nav-item.active { background: rgba(108,99,255,.12); color: var(--text); }
.nav-item.active { color: var(--accent); font-weight: 500; }
.nav-icon { font-size: 16px; width: 20px; text-align: center; }
.sidebar-footer { padding: 16px; border-top: 1px solid var(--border); }
.main { margin-left: 240px; flex: 1; padding: 32px; }
</style>
