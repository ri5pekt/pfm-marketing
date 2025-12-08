<template>
    <router-view />
</template>

<script setup>
import { onMounted } from "vue";
import { useAuthStore } from "@/store/authStore";

const authStore = useAuthStore();

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
</style>
