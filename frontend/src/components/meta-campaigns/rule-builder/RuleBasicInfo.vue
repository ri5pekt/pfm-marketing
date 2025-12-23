<template>
    <div class="form-section">
        <h3 class="section-title">1. Basic Info</h3>
        <div class="field">
            <label>Rule Name *</label>
            <InputText
                :modelValue="modelValue.name"
                @update:modelValue="update('name', $event)"
                class="w-full"
                :class="{ 'p-invalid': errors.name }"
            />
            <small v-if="errors.name" class="p-error">{{ errors.name }}</small>
        </div>
        <div class="field">
            <label>Description</label>
            <Textarea
                :modelValue="modelValue.description"
                @update:modelValue="update('description', $event)"
                class="w-full"
                rows="3"
            />
        </div>
        <div v-if="modelValue.ruleLevel" class="field">
            <div class="flex align-items-center gap-2">
                <InputSwitch
                    :modelValue="modelValue.enabled"
                    @update:modelValue="update('enabled', $event)"
                    inputId="enabled"
                />
                <label for="enabled" class="field-label">Enabled</label>
            </div>
        </div>
    </div>
</template>

<script setup>
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import InputSwitch from "primevue/inputswitch";

const props = defineProps({
    modelValue: {
        type: Object,
        required: true,
    },
    errors: {
        type: Object,
        default: () => ({}),
    },
});

const emit = defineEmits(["update:modelValue"]);

function update(field, value) {
    emit("update:modelValue", {
        ...props.modelValue,
        [field]: value,
    });
}
</script>

<style scoped>
.form-section {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.5rem;
    background-color: #f9fafb;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}

.section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 1rem 0;
}

.field {
    margin-bottom: 1rem;
}

.field:last-child {
    margin-bottom: 0;
}

.field label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #374151;
}

.field-label {
    margin: 0;
    font-weight: 600;
    color: #374151;
}

.p-error {
    color: #ef4444;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}
</style>
