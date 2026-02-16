<template>
    <div class="field">
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
</style>
