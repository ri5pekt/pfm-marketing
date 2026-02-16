<template>
    <div class="field">
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
</style>
