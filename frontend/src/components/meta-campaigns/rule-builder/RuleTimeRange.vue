<template>
    <div v-if="modelValue.ruleLevel" class="form-section">
        <h3 class="section-title">3. Time Range (Data Window)</h3>
        <div class="fields-row">
            <div class="field field-half">
                <label>Time Unit *</label>
                <Select
                    :modelValue="modelValue.timeRangeUnit"
                    @update:modelValue="update('timeRangeUnit', $event)"
                    :options="timeRangeUnitOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select time unit"
                    class="w-full"
                    :class="{ 'p-invalid': errors.timeRangeUnit }"
                />
                <small v-if="errors.timeRangeUnit" class="p-error">{{ errors.timeRangeUnit }}</small>
            </div>
            <div class="field field-half">
                <label>Amount *</label>
                <InputNumber
                    :modelValue="modelValue.timeRangeAmount"
                    @update:modelValue="update('timeRangeAmount', $event)"
                    :min="1"
                    placeholder="Enter amount"
                    class="w-full"
                    :class="{ 'p-invalid': errors.timeRangeAmount }"
                    :disabled="modelValue.timeRangeUnit === 'today'"
                />
                <small v-if="errors.timeRangeAmount" class="p-error">{{ errors.timeRangeAmount }}</small>
                <small v-if="modelValue.timeRangeUnit === 'today'" class="p-text-secondary">
                    (Automatically set to 1 day for today only)
                </small>
            </div>
        </div>
        <div class="field">
            <div class="flex align-items-center gap-2">
                <InputSwitch
                    :modelValue="modelValue.excludeToday"
                    @update:modelValue="update('excludeToday', $event)"
                    inputId="excludeToday"
                    :disabled="
                        modelValue.timeRangeUnit === 'minutes' ||
                        modelValue.timeRangeUnit === 'hours' ||
                        modelValue.timeRangeUnit === 'today'
                    "
                />
                <label for="excludeToday" class="field-label">Exclude today</label>
            </div>
            <small
                class="p-text-secondary"
                v-if="modelValue.timeRangeUnit === 'minutes' || modelValue.timeRangeUnit === 'hours'"
            >
                (No effect for minutes or hours)
            </small>
            <small class="p-text-secondary" v-if="modelValue.timeRangeUnit === 'today'">
                (Disabled for today only)
            </small>
        </div>
    </div>
</template>

<script setup>
import Select from 'primevue/select'
import InputNumber from 'primevue/inputnumber'
import InputSwitch from 'primevue/inputswitch'

const props = defineProps({
    modelValue: {
        type: Object,
        required: true,
    },
    errors: {
        type: Object,
        default: () => ({}),
    },
})

const emit = defineEmits(['update:modelValue'])

const timeRangeUnitOptions = [
    { label: 'Minutes', value: 'minutes' },
    { label: 'Hours', value: 'hours' },
    { label: 'Days', value: 'days' },
    { label: 'Today only', value: 'today' },
]

function update(field, value) {
    emit('update:modelValue', {
        ...props.modelValue,
        [field]: value,
    })
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

.fields-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}

.field {
    margin-bottom: 1rem;
}

.field:last-child {
    margin-bottom: 0;
}

.field-half {
    flex: 1;
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

.p-text-secondary {
    color: #6b7280;
    font-size: 0.875rem;
}
</style>

