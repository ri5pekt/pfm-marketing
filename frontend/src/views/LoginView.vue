<template>
    <div class="login-container">
        <div class="login-card-wrapper">
            <Card class="login-card">
                <template #header>
                    <div class="login-header">
                        <h1>PFM Marketing</h1>
                        <p>Sign in to your account</p>
                    </div>
                </template>
                <template #content>
                    <form @submit.prevent="handleLogin" class="login-form">
                        <div class="input-group">
                            <label class="field-label">
                                <i class="pi pi-envelope" />
                                <span>Email Address</span>
                            </label>
                            <InputText
                                v-model="email"
                                type="email"
                                placeholder="Enter your email"
                                class="w-full"
                                :class="{ 'p-invalid': errors.email }"
                                required
                            />
                            <small v-if="errors.email" class="p-error">{{ errors.email }}</small>
                        </div>
                        <div class="input-group">
                            <label class="field-label">
                                <i class="pi pi-lock" />
                                <span>Password</span>
                            </label>
                            <Password
                                v-model="password"
                                placeholder="Enter your password"
                                :feedback="false"
                                toggleMask
                                class="w-full"
                                :class="{ 'p-invalid': errors.password }"
                                :inputClass="'w-full'"
                                required
                            />
                            <small v-if="errors.password" class="p-error">{{ errors.password }}</small>
                        </div>
                        <Button type="submit" class="w-full login-button" :loading="loading">
                            <i class="pi pi-arrow-right" />
                            <span>Sign In</span>
                        </Button>
                    </form>
                </template>
            </Card>
        </div>
        <Toast />
    </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Password from "primevue/password";
import Button from "primevue/button";
import Toast from "primevue/toast";
import { useAuthStore } from "@/store/authStore";

const router = useRouter();
const toast = useToast();
const authStore = useAuthStore();

const email = ref("");
const password = ref("");
const loading = ref(false);
const errors = ref({});

async function handleLogin() {
    errors.value = {};

    if (!email.value) {
        errors.value.email = "Email is required";
        return;
    }
    if (!password.value) {
        errors.value.password = "Password is required";
        return;
    }

    loading.value = true;
    try {
        const result = await authStore.login(email.value, password.value);
        if (result.success) {
            toast.add({
                severity: "success",
                summary: "Success",
                detail: "Logged in successfully",
                life: 3000,
            });
            router.push({ name: "dashboard" });
        } else {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: result.error || "Login failed",
                life: 5000,
            });
        }
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: error.message || "Login failed",
            life: 5000,
        });
    } finally {
        loading.value = false;
    }
}
</script>

<style scoped>
.login-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #0099ff 0%, #0064e0 100%);
    padding: 20px;
}

.login-card-wrapper {
    width: 100%;
    max-width: 420px;
}

.login-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    border: none;
    overflow: hidden;
}

.login-header {
    background: linear-gradient(135deg, #0099ff 0%, #0064e0 100%);
    padding: 2rem;
    border-radius: 16px 16px 0 0;
    text-align: center;
    color: white;
}

.login-header h1 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.login-header p {
    font-size: 0.95rem;
    opacity: 0.9;
}

.login-form {
    padding: 2rem;
}

.input-group {
    margin-bottom: 1.5rem;
}

.field-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
}

.field-label i {
    font-size: 1rem;
    color: #6b7280;
}

.input-group :deep(.p-inputtext),
.input-group :deep(.p-password) {
    width: 100%;
}

.input-group :deep(.p-password-input) {
    width: 100%;
}

.login-button {
    margin-top: 1rem;
    padding: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.login-button.p-button {
    background: #4ade80;
    border: none;
    color: white;
}

.login-button.p-button:hover {
    background: #22c55e;
}

.login-button :deep(.p-button-label) {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.login-button i {
    font-size: 1rem;
}

.p-error {
    display: block;
    margin-top: 0.25rem;
}
</style>
