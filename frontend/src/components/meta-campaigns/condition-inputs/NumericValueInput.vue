<template>
    <InputNumber
        :modelValue="value"
        @update:modelValue="$emit('update:value', $event)"
        :step="0.01"
        :minFractionDigits="0"
        :maxFractionDigits="6"
        placeholder="Enter value"
        class="w-full value-input"
    />
</template>

<script setup>
import InputNumber from 'primevue/inputnumber';

defineProps({
    value: {
        type: [Number, null],
        default: null,
    },
});

defineEmits(['update:value']);
</script>

<style scoped>
.value-input {
    width: 100%;
}
</style>
