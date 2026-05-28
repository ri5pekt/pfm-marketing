<template>
    <div class="settings-main">
        <div class="page-header">
            <div>
                <h1>Main Settings</h1>
                <p>Customize the application title and brand color.</p>
            </div>
        </div>

        <div class="settings-card">
            <div class="settings-section">
                <h3>Application Title</h3>
                <p class="section-desc">This title appears in the header, login page, and browser tab.</p>
                <InputText
                    v-model="form.title"
                    placeholder="e.g. My Marketing Tool"
                    class="w-full title-input"
                    :disabled="!authStore.isAdmin"
                />
            </div>

            <div class="settings-section">
                <h3>Brand Color</h3>
                <p class="section-desc">Sets the primary color used throughout the app. A gradient is automatically derived from this color.</p>
                <div class="color-row">
                    <div class="color-picker-wrapper">
                        <input
                            type="color"
                            v-model="form.primary_color"
                            class="color-input"
                            :disabled="!authStore.isAdmin"
                        />
                        <InputText
                            v-model="form.primary_color"
                            placeholder="#0099ff"
                            class="color-hex-input"
                            :disabled="!authStore.isAdmin"
                            @input="syncColorFromText"
                        />
                    </div>
                </div>
                <div class="gradient-preview" :style="{ background: previewGradient }">
                    <span>Gradient Preview</span>
                </div>
            </div>

            <div class="settings-footer">
                <span v-if="!authStore.isAdmin" class="admin-note">
                    <i class="pi pi-lock"></i>
                    Only admins can save changes
                </span>
                <Button
                    label="Save Settings"
                    icon="pi pi-check"
                    :loading="saving"
                    :disabled="!authStore.isAdmin"
                    @click="handleSave"
                />
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useAuthStore } from '@/store/authStore'
import { useAppSettingsStore } from '@/store/appSettingsStore'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'

const authStore = useAuthStore()
const appSettingsStore = useAppSettingsStore()
const toast = useToast()

const saving = ref(false)
const form = ref({
    title: appSettingsStore.appTitle,
    primary_color: appSettingsStore.primaryColor,
})

function darkenHex(hex, amount = 20) {
    const clean = hex.replace('#', '')
    if (clean.length !== 6) return hex
    const r = parseInt(clean.substring(0, 2), 16) / 255
    const g = parseInt(clean.substring(2, 4), 16) / 255
    const b = parseInt(clean.substring(4, 6), 16) / 255

    const max = Math.max(r, g, b)
    const min = Math.min(r, g, b)
    let h, s, l = (max + min) / 2

    if (max === min) {
        h = s = 0
    } else {
        const d = max - min
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
        switch (max) {
            case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break
            case g: h = ((b - r) / d + 2) / 6; break
            case b: h = ((r - g) / d + 4) / 6; break
        }
    }

    l = Math.max(0, l - amount / 100)

    function hue2rgb(p, q, t) {
        if (t < 0) t += 1
        if (t > 1) t -= 1
        if (t < 1 / 6) return p + (q - p) * 6 * t
        if (t < 1 / 2) return q
        if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6
        return p
    }

    let rOut, gOut, bOut
    if (s === 0) {
        rOut = gOut = bOut = l
    } else {
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s
        const p = 2 * l - q
        rOut = hue2rgb(p, q, h + 1 / 3)
        gOut = hue2rgb(p, q, h)
        bOut = hue2rgb(p, q, h - 1 / 3)
    }

    const toHex = (x) => Math.round(x * 255).toString(16).padStart(2, '0')
    return `#${toHex(rOut)}${toHex(gOut)}${toHex(bOut)}`
}

const previewGradient = computed(() => {
    const color = form.value.primary_color
    if (!color || color.length < 4) return 'linear-gradient(135deg, #0099ff 0%, #0064e0 100%)'
    const end = darkenHex(color, 20)
    return `linear-gradient(135deg, ${color} 0%, ${end} 100%)`
})

function syncColorFromText(event) {
    const val = event.target.value
    if (/^#[0-9a-fA-F]{6}$/.test(val)) {
        form.value.primary_color = val
    }
}

async function handleSave() {
    if (!form.value.title?.trim()) {
        toast.add({ severity: 'warn', summary: 'Validation', detail: 'Title cannot be empty', life: 3000 })
        return
    }
    saving.value = true
    try {
        await appSettingsStore.save(form.value.title.trim(), form.value.primary_color)
        toast.add({ severity: 'success', summary: 'Saved', detail: 'Settings updated successfully', life: 3000 })
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: e.message, life: 5000 })
    } finally {
        saving.value = false
    }
}

// Sync form when store initializes
watch(() => appSettingsStore.appTitle, (val) => { form.value.title = val })
watch(() => appSettingsStore.primaryColor, (val) => { form.value.primary_color = val })
</script>

<style scoped>
.settings-main {
    max-width: 640px;
    margin: 0 auto;
}

.page-header {
    margin-bottom: 2rem;
}

.page-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 0.25rem;
}

.page-header p {
    color: #6b7280;
    font-size: 0.95rem;
}

.settings-card {
    background: white;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    gap: 2rem;
}

.settings-section h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 0.25rem;
}

.section-desc {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 0.75rem;
}

.title-input {
    font-size: 1rem;
}

.color-row {
    margin-bottom: 1rem;
}

.color-picker-wrapper {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.color-input {
    width: 48px;
    height: 42px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 2px;
    cursor: pointer;
    background: none;
    flex-shrink: 0;
}

.color-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.color-hex-input {
    width: 140px;
    font-family: monospace;
}

.gradient-preview {
    height: 48px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 0.875rem;
    letter-spacing: 0.02em;
    transition: background 0.3s ease;
}

.settings-footer {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 1rem;
    padding-top: 0.5rem;
    border-top: 1px solid #f3f4f6;
}

.admin-note {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    color: #9ca3af;
}
</style>
