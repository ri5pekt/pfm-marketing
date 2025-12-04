import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/authStore'
import LoginView from '@/views/LoginView.vue'
import AppShell from '@/views/AppShell.vue'
import DashboardView from '@/views/DashboardView.vue'
import MetaCampaignsView from '@/views/MetaCampaignsView.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { public: true }
  },
  {
    path: '/',
    component: AppShell,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: DashboardView
      },
      {
        path: '/meta-campaigns',
        name: 'meta-campaigns',
        component: MetaCampaignsView
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Check if token exists in localStorage (source of truth)
  const tokenInStorage = localStorage.getItem('pfm_token')

  // If no token in storage, ensure state is cleared
  if (!tokenInStorage) {
    if (authStore.user) {
      authStore.logout()
    }
    // If trying to access protected route, redirect to login
    if (to.meta.requiresAuth) {
      return next({ name: 'login' })
    }
    // Allow access to public routes
    return next()
  }

  // If there's a token but no user data, fetch it first
  if (tokenInStorage && !authStore.user && !authStore.loadingUser) {
    try {
      await authStore.fetchMe()
    } catch (error) {
      console.error('Failed to fetch user on route guard:', error)
      // fetchMe handles clearing token on 401 errors
    }
  }

  // Wait if user is currently being loaded (from another navigation)
  if (authStore.loadingUser) {
    // Wait for loading to complete (max 5 seconds)
    let waitCount = 0
    while (authStore.loadingUser && waitCount < 100) {
      await new Promise(resolve => setTimeout(resolve, 50))
      waitCount++
    }
  }

  // Check authentication status after loading completes
  const hasToken = !!tokenInStorage
  const hasUser = !!authStore.user
  const isAuthenticated = hasToken && hasUser

  if (to.meta.public) {
    // If authenticated and trying to access login, redirect to dashboard
    if (isAuthenticated) {
      return next({ name: 'dashboard' })
    }
    return next()
  } else if (to.meta.requiresAuth) {
    // Must be authenticated to access protected routes
    if (isAuthenticated) {
      return next()
    }
    // Not authenticated, redirect to login
    return next({ name: 'login' })
  }

  return next()
})

export default router

