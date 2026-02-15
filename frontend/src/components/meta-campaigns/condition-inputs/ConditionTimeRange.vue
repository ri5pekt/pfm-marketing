<template>
    <div class="condition-time-range">
        <div class="time-range-header">
            <div class="flex align-items-center gap-2">
                <InputSwitch
                    :modelValue="useCustomTimeRange"
                    @update:modelValue="$emit('toggle-custom', $event)"
                    :inputId="`useCustomTimeRange-${conditionIndex}`"
                />
                <label :for="`useCustomTimeRange-${conditionIndex}`" class="field-label">
                    Use custom time range
                </label>
            </div>
            <small v-if="!useCustomTimeRange" class="p-text-secondary">
                Using global time range: {{ globalTimeRangeLabel }}
            </small>
        </div>

        <div v-if="useCustomTimeRange" class="time-range-fields">
            <div class="fields-row">
                <div class="field field-half">
                    <label>Time Unit *</label>
                    <Select
                        :modelValue="timeRange.unit"
                        @update:modelValue="$emit('update-time-range', 'unit', $event)"
                        :options="timeRangeUnitOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="Select time unit"
                        class="w-full"
                    />
                </div>
                <div class="field field-half">
                    <label>Amount *</label>
                    <InputNumber
                        :modelValue="timeRange.amount"
                        @update:modelValue="$emit('update-time-range', 'amount', $event)"
                        :min="1"
                        placeholder="Enter amount"
                        class="w-full"
                        :disabled="timeRange.unit === 'today'"
                    />
                    <small v-if="timeRange.unit === 'today'" class="p-text-secondary">
                        (Automatically set to 1 day for today only)
                    </small>
                </div>
            </div>
            <div class="field">
                <div class="flex align-items-center gap-2">
                    <InputSwitch
                        :modelValue="timeRange.exclude_today"
                        @update:modelValue="$emit('update-time-range', 'exclude_today', $event)"
                        :inputId="`conditionExcludeToday-${conditionIndex}`"
                        :disabled="
                            timeRange.unit === 'minutes' ||
                            timeRange.unit === 'hours' ||
                            timeRange.unit === 'today'
                        "
                    />
                    <label :for="`conditionExcludeToday-${conditionIndex}`" class="field-label">
                        Exclude today
                    </label>
                </div>
                <small
                    class="p-text-secondary"
                    v-if="timeRange.unit === 'minutes' || timeRange.unit === 'hours'"
                >
                    (No effect for minutes or hours)
                </small>
                <small class="p-text-secondary" v-if="timeRange.unit === 'today'">
                    (Disabled for today only)
                </small>
            </div>
        </div>
    </div>
</template>

<script setup>
import Select from 'primevue/select';
import InputNumber from 'primevue/inputnumber';
import InputSwitch from 'primevue/inputswitch';

defineProps({
    conditionIndex: {
        type: Number,
        required: true,
    },
    useCustomTimeRange: {
        type: Boolean,
        default: false,
    },
    timeRange: {
        type: Object,
        required: true,
    },
    timeRangeUnitOptions: {
        type: Array,
        required: true,
    },
    globalTimeRangeLabel: {
        type: String,
        default: 'Not set',
    },
});

defineEmits(['toggle-custom', 'update-time-range']);
</script>

<style scoped>
.condition-time-range {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
}

.time-range-header {
    margin-bottom: 1rem;
}

.flex {
    display: flex;
}

.align-items-center {
    align-items: center;
}

.gap-2 {
    gap: 0.5rem;
}

.field-label {
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--text-color);
    cursor: pointer;
}

.p-text-secondary {
    color: var(--text-color-secondary);
    font-size: 0.8125rem;
    display: block;
    margin-top: 0.25rem;
}

.time-range-fields {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.fields-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

.field {
    display: flex;
    flex-direction: column;
}

.field label {
    font-weight: 600;
    font-size: 0.875rem;
    margin-bottom: 0.375rem;
    color: var(--text-color);
}

.field-half {
    min-width: 0;
}

@media (max-width: 640px) {
    .fields-row {
        grid-template-columns: 1fr;
    }
}
</style>
