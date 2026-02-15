<template>
    <div class="field">
        <div class="field-label-row">
            <label>Field *</label>
            <span></span>
        </div>
        <Select
            :modelValue="field"
            @update:modelValue="$emit('update:field', $event)"
            :options="availableConditionFields"
            optionLabel="label"
            optionValue="value"
            placeholder="Select field"
            class="w-full"
        />
    </div>
</template>

<script setup>
import Select from "primevue/select";

defineProps({
    field: {
        type: String,
        default: null,
    },
    availableConditionFields: {
        type: Array,
        required: true,
    },
});

defineEmits(["update:field"]);
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
