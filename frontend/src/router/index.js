import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPasswordView.vue'),
  },
  {
    path: '/accept-invitation',
    name: 'AcceptInvitation',
    component: () => import('@/views/AcceptInvitationView.vue'),
  },
  {
    path: '/',
    component: () => import('@/components/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'Dashboard', component: () => import('@/views/DashboardView.vue') },
      { path: 'organizations', name: 'Organizations', component: () => import('@/views/OrganizationsView.vue') },
      { path: 'users', name: 'Users', component: () => import('@/views/UsersView.vue') },
      { path: 'roles', name: 'Roles', component: () => import('@/views/RolesView.vue') },
      { path: 'permissions', name: 'Permissions', component: () => import('@/views/PermissionsView.vue') },
      { path: 'profile', name: 'Profile', component: () => import('@/views/ProfileView.vue') },
      { path: 'my-access', name: 'MyAccess', component: () => import('@/views/MyAccessView.vue') },
      { path: 'recording', name: 'Recording', component: () => import('@/views/RecordingView.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  const refreshToken = localStorage.getItem('refreshToken')

  // Restore session from refresh token if user not yet loaded
  if (refreshToken && !store.getters['auth/isLoggedIn']) {
    await store.dispatch('auth/restoreSession')
  }

  const isLoggedIn = store.getters['auth/isLoggedIn']

  if (to.meta.requiresAuth && !isLoggedIn) return next('/login')
  if (to.meta.guest && isLoggedIn) return next('/')
  next()
})

export default router
