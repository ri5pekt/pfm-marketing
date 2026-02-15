<template>
    <InputText
        :modelValue="value"
        @update:modelValue="$emit('update:value', $event)"
        :placeholder="placeholder"
        class="w-full value-input"
    />
</template>

<script setup>
import InputText from 'primevue/inputtext';

defineProps({
    value: {
        type: [String, null],
        default: null,
    },
    placeholder: {
        type: String,
        default: 'Enter value',
    },
});

defineEmits(['update:value']);
</script>

<style scoped>
.value-input {
    width: 100%;
}
</style>
