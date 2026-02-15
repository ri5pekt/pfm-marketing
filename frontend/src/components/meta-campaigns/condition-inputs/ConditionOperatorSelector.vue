<template>
    <div class="field">
        <div class="field-label-row">
            <label>Operator *</label>
            <span></span>
        </div>
        <Select
            :modelValue="operator"
            @update:modelValue="$emit('update:operator', $event)"
            :options="operatorOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Select operator"
            class="w-full"
        />
    </div>
</template>

<script setup>
import Select from "primevue/select";

defineProps({
    operator: {
        type: String,
        default: null,
    },
    operatorOptions: {
        type: Array,
        required: true,
    },
});

defineEmits(["update:operator"]);
</script>

<style scoped>
.field {
    min-width: 0;
    display: flex;
    flex-direction: column;
}

.field-label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.375rem;
}

label {
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--text-color);
}
</style>
