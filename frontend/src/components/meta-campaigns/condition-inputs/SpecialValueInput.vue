<template>
    <div>
        <div class="special-value-row">
            <InputText
                class="value-input special-value"
                :modelValue="baseValue"
                @update:modelValue="updateBase"
                placeholder="__daily_budget__"
            />
            <div class="multiplier">
                <span class="multiplier-prefix">×</span>
                <InputNumber
                    :modelValue="multiplier"
                    @update:modelValue="updateMultiplier"
                    :min="0"
                    :step="0.01"
                    :minFractionDigits="0"
                    :maxFractionDigits="6"
                    placeholder="1"
                    class="multiplier-input"
                />
            </div>
        </div>
        <small class="special-value-label">{{ valueLabel }}</small>
    </div>
</template>

<script setup>
import { computed } from 'vue';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import { getSpecialBase, getSpecialMul, getSpecialValueLabel } from '@/utils/specialValues';

const props = defineProps({
    value: {
        type: [Object, String, null],
        default: null,
    },
});

const emit = defineEmits(['update:value']);

const baseValue = computed(() => {
    return getSpecialBase(props.value);
});

const multiplier = computed(() => {
    return getSpecialMul(props.value);
});

const valueLabel = computed(() => {
    return getSpecialValueLabel(props.value);
});

function updateBase(base) {
    const baseStr = base === null || base === undefined ? '' : String(base);
    
    // Normalize to object format
    if (typeof props.value === 'object' && props.value) {
        emit('update:value', {
            ...props.value,
            base: baseStr,
            mul: props.value.mul !== undefined ? props.value.mul : 1,
        });
    } else {
        emit('update:value', { base: baseStr, mul: 1 });
    }
}

function updateMultiplier(mul) {
    const safeMul = mul === null || mul === undefined || mul === '' ? 1 : Number(mul);
    
    // Normalize to object format
    if (typeof props.value === 'object' && props.value) {
        emit('update:value', {
            ...props.value,
            mul: safeMul,
        });
    } else {
        emit('update:value', { base: props.value || '', mul: safeMul });
    }
}
</script>

<style scoped>
.special-value-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.value-input {
    flex: 1;
    min-width: 0;
}

.special-value {
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
}

.multiplier {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    flex-shrink: 0;
}

.multiplier-prefix {
    font-weight: 600;
    color: var(--text-color-secondary);
}

.multiplier-input {
    width: 80px;
}

.special-value-label {
    display: block;
    margin-top: 0.375rem;
    color: var(--text-color-secondary);
    font-size: 0.8125rem;
}
</style>
