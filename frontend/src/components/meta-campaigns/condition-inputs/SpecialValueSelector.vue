<template>
    <div class="special-value-selector">
        <Button
            v-if="availableSpecialValues.length > 0"
            label="Add Special Value"
            severity="secondary"
            outlined
            @click="toggleMenu"
            type="button"
            class="special-value-button-inline"
            :disabled="!field"
            size="small"
        />

        <OverlayPanel ref="menuRef" :dismissable="true">
            <div class="special-values-menu">
                <div class="special-values-title">Special Values</div>
                <div
                    v-for="(special, idx) in availableSpecialValues"
                    :key="idx"
                    class="special-value-item"
                    @click="selectValue(special.value)"
                >
                    <div class="special-value-item-label">{{ special.label }}</div>
                    <div class="special-value-item-code">{{ special.value }}</div>
                    <div class="special-value-item-desc">
                        {{ special.description }}
                    </div>
                </div>
            </div>
        </OverlayPanel>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import Button from 'primevue/button';
import OverlayPanel from 'primevue/overlaypanel';

defineProps({
    field: {
        type: String,
        default: null,
    },
    availableSpecialValues: {
        type: Array,
        default: () => [],
    },
});

const emit = defineEmits(['select']);

const menuRef = ref(null);

function toggleMenu(event) {
    if (menuRef.value) {
        menuRef.value.toggle(event);
    }
}

function selectValue(value) {
    emit('select', value);
    if (menuRef.value) {
        menuRef.value.hide();
    }
}
</script>

<style scoped>
.special-value-button-inline {
    height: auto;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
}

.special-values-menu {
    max-width: 400px;
}

.special-values-title {
    font-weight: 600;
    font-size: 0.9375rem;
    margin-bottom: 0.75rem;
    color: var(--text-color);
}

.special-value-item {
    padding: 0.75rem;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.special-value-item:hover {
    background: var(--surface-50);
    border-color: var(--primary-color);
}

.special-value-item:last-child {
    margin-bottom: 0;
}

.special-value-item-label {
    font-weight: 600;
    font-size: 0.875rem;
    margin-bottom: 0.25rem;
    color: var(--text-color);
}

.special-value-item-code {
    font-family: 'Courier New', monospace;
    font-size: 0.8125rem;
    color: var(--primary-color);
    background: var(--primary-50);
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    display: inline-block;
    margin-bottom: 0.375rem;
}

.special-value-item-desc {
    font-size: 0.8125rem;
    color: var(--text-color-secondary);
}
</style>
