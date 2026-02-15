<template>
    <Select
        :modelValue="value"
        @update:modelValue="$emit('update:value', $event)"
        :options="statusOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Select status"
        class="w-full value-input"
    />
</template>

<script setup>
import Select from 'primevue/select';

defineProps({
    value: {
        type: [String, null],
        default: null,
    },
    statusOptions: {
        type: Array,
        required: true,
    },
});

defineEmits(['update:value']);
</script>

<style scoped>
.value-input {
    width: 100%;
}
</style>
