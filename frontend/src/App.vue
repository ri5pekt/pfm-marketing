<template>
    <div v-if="appLoading" class="app-loading-overlay">
        <div class="app-loading-content">
            <ProgressSpinner />
            <p class="app-loading-text">Loading application...</p>
        </div>
    </div>
    <router-view v-else />
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import { useAuthStore } from "@/store/authStore";
import ProgressSpinner from "primevue/progressspinner";

const authStore = useAuthStore();
const appLoading = ref(true);

onMounted(async () => {
    // Validate token on app startup if one exists
    const tokenInStorage = localStorage.getItem("pfm_token");
    if (tokenInStorage && !authStore.user && !authStore.loadingUser) {
        try {
            await authStore.fetchMe();
        } catch (error) {
            // If validation fails, clear everything
            authStore.logout();
        }
    } else if (!tokenInStorage) {
        // Ensure state is cleared if no token
        if (authStore.user || authStore.token?.value) {
            authStore.logout();
        }
    }

    // Hide loading after initialization completes
    // Small delay to ensure smooth transition
    setTimeout(() => {
        appLoading.value = false;
    }, 300);
});
</script>

<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: "Inter", sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

#app {
    min-height: 100vh;
}

.app-loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(255, 255, 255, 0.95);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.app-loading-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
}

.app-loading-content :deep(.p-progress-spinner-circle) {
    stroke: #0099FF;
}

.app-loading-text {
    font-size: 1rem;
    color: #6b7280;
    font-weight: 500;
    margin: 0;
}
</style>
