<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="header-left">
        <div class="logo">
          <i class="pi pi-chart-line"></i>
        </div>
        <div class="app-title">
          <h2>PFM Marketing</h2>
          <span class="version">v1.0.0</span>
        </div>
      </div>
      <div class="header-right">
        <div class="user-info">
          <div class="user-avatar">
            <i class="pi pi-user"></i>
          </div>
          <div class="user-details">
            <span class="user-email">{{ userEmail || (authStore.loadingUser ? 'Loading...' : '') }}</span>
            <span class="user-role" :class="{ 'role-admin': authStore.isAdmin }">
              {{ authStore.isAdmin ? 'Admin' : 'User' }}
            </span>
          </div>
        </div>
        <Button
          label="Logout"
          icon="pi pi-sign-out"
          severity="secondary"
          outlined
          @click="handleLogout"
        />
      </div>
    </header>
    <div class="app-body">
      <aside class="app-sidebar">
        <nav class="sidebar-nav">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ active: $route.path === item.path }"
          >
            <i :class="item.icon"></i>
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
      </aside>
      <main class="app-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import { useAuthStore } from '@/store/authStore'

const router = useRouter()
const toast = useToast()
const authStore = useAuthStore()

// Create a local computed for email
const userEmail = computed(() => authStore.user?.email || '')

onMounted(async () => {
  // Ensure user is loaded when component mounts
  if (authStore.token && !authStore.user && !authStore.loadingUser) {
    await authStore.fetchMe()
  }
})

const menuItems = ref([
  {
    path: '/',
    label: 'Dashboard',
    icon: 'pi pi-home'
  },
  {
    path: '/meta-campaigns',
    label: 'Meta Campaigns',
    icon: 'pi pi-facebook'
  }
])

async function handleLogout() {
  authStore.logout()
  toast.add({
    severity: 'info',
    summary: 'Logged out',
    detail: 'You have been logged out',
    life: 3000
  })
  // Force immediate redirect
  await router.push({ name: 'login' })
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #0099FF 0%, #0064E0 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.25rem;
}

.app-title h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.version {
  font-size: 0.75rem;
  color: #6b7280;
  margin-left: 0.5rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: #f3f4f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-email {
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
}

.user-role {
  font-size: 0.75rem;
  color: #6b7280;
}

.role-admin {
  color: #0099FF;
  font-weight: 600;
}

.user-email-display {
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
  margin-right: 0.5rem;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-sidebar {
  width: 260px;
  background: white;
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-nav {
  padding: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  color: #4b5563;
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #f9fafb;
  color: #1f2937;
}

.nav-item.active {
  background: linear-gradient(135deg, #0099FF 0%, #0064E0 100%);
  color: white;
}

.nav-item i {
  font-size: 1.125rem;
}

.app-main {
  flex: 1;
  overflow-y: auto;
  background: #f9fafb;
  padding: 2rem;
}
</style>

