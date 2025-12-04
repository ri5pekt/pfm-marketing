import { reactive, computed } from 'vue'
import { loginApi, meApi } from '@/api/authApi'

// Helper to get token from localStorage (source of truth)
function getTokenFromStorage() {
  return localStorage.getItem('pfm_token')
}

const state = reactive({
  user: null,
  loadingUser: false
})

export function useAuthStore() {
  const token = computed(() => getTokenFromStorage())
  const isAuthenticated = computed(() => !!token.value && !!state.user)

  const isAdmin = computed(() => state.user?.is_admin || false)

  async function login(email, password) {
    try {
      console.log('Attempting login with:', email)
      const response = await loginApi(email, password)
      console.log('Login response received:', response)
      localStorage.setItem('pfm_token', response.access_token)
      await fetchMe()
      return { success: true }
    } catch (error) {
      console.error('Login error:', error)
      return { success: false, error: error.message || 'Login failed' }
    }
  }

  function logout() {
    // Clear everything synchronously
    localStorage.removeItem('pfm_token')
    state.user = null
    state.loadingUser = false
  }

  async function fetchMe() {
    const currentToken = getTokenFromStorage()
    if (!currentToken) {
      state.user = null
      return
    }

    state.loadingUser = true
    try {
      const userData = await meApi()
      console.log('User data received:', userData)
      state.user = userData
      console.log('User state set:', state.user)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      // Only clear token if it's a 401 (unauthorized) error
      // Other errors (network, etc.) shouldn't log us out
      if (error.status === 401 || (error.message && error.message.includes('401'))) {
        console.log('Token invalid (401), clearing...')
        localStorage.removeItem('pfm_token')
        state.user = null
      } else {
        // For other errors, keep the token but don't set user
        // This allows retry on next navigation
        console.log('Non-auth error, keeping token for retry:', error.message)
      }
    } finally {
      state.loadingUser = false
    }
  }

  // Return state.user directly instead of wrapping in computed
  // This ensures better reactivity
  return {
    token,
    get user() { return state.user },
    get loadingUser() { return state.loadingUser },
    isAuthenticated,
    isAdmin,
    login,
    logout,
    fetchMe
  }
}

