<template>
    <div class="cpp-winning-days-inputs">
        <div class="value-input">
            <label class="threshold-label">Winning Days Count *</label>
            <InputNumber
                :modelValue="value"
                @update:modelValue="$emit('update:value', $event)"
                :min="0"
                :step="1"
                :minFractionDigits="0"
                :maxFractionDigits="0"
                placeholder="Enter number of days"
                class="w-full"
            />
        </div>
        <div class="threshold-input">
            <label class="threshold-label">Threshold (CPP) *</label>
            <InputNumber
                :modelValue="threshold"
                @update:modelValue="$emit('update:threshold', $event)"
                :step="0.01"
                :min="0"
                :minFractionDigits="0"
                :maxFractionDigits="6"
                placeholder="Enter CPP threshold"
                class="w-full"
            />
        </div>
        <small class="p-text-secondary"> Counts days where CPP was below the threshold </small>
    </div>
</template>

<script setup>
import InputNumber from 'primevue/inputnumber';

defineProps({
    value: {
        type: [Number, null],
        default: null,
    },
    threshold: {
        type: [Number, null],
        default: null,
    },
});

defineEmits(['update:value', 'update:threshold']);
</script>

<style scoped>
.cpp-winning-days-inputs {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.threshold-label {
    display: block;
    margin-bottom: 0.375rem;
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--text-color);
}

.p-text-secondary {
    color: var(--text-color-secondary);
    font-size: 0.8125rem;
}
</style>
