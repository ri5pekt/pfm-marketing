<template>
    <OverlayPanel ref="overlayRef" :dismissable="true">
        <div class="special-values-menu">
            <div class="special-values-title">Special Values</div>
            <div
                v-for="(special, idx) in availableSpecialValues"
                :key="idx"
                class="special-value-item"
                @click="handleSelect(special.value)"
            >
                <div class="special-value-item-label">{{ special.label }}</div>
                <div class="special-value-item-code">{{ special.value }}</div>
                <div class="special-value-item-desc">
                    {{ special.description }}
                </div>
            </div>
        </div>
    </OverlayPanel>
</template>

<script setup>
import { ref } from "vue";
import OverlayPanel from "primevue/overlaypanel";

const props = defineProps({
    availableSpecialValues: {
        type: Array,
        required: true,
    },
});

const emit = defineEmits(["select", "close"]);

const overlayRef = ref(null);

function toggle(event) {
    if (overlayRef.value) {
        overlayRef.value.toggle(event);
    }
}

function hide() {
    if (overlayRef.value) {
        overlayRef.value.hide();
    }
}

function handleSelect(specialValue) {
    emit("select", specialValue);
    hide();
}

// Expose methods for parent component
defineExpose({
    toggle,
    hide,
});
</script>

<style scoped>
.special-values-menu {
    min-width: 300px;
    max-width: 400px;
}

.special-values-title {
    font-weight: 600;
    padding: 0.5rem;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 0.5rem;
}

.special-value-item {
    padding: 0.75rem;
    cursor: pointer;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.special-value-item:hover {
    background-color: #f3f4f6;
}

.special-value-item-label {
    font-weight: 500;
    color: #1f2937;
    margin-bottom: 0.25rem;
}

.special-value-item-code {
    font-family: monospace;
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 0.25rem;
}

.special-value-item-desc {
    font-size: 0.75rem;
    color: #9ca3af;
}
</style>

