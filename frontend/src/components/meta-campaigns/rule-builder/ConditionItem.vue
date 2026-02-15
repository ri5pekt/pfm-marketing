<template>
    <div class="condition-item">
        <div class="condition-header">
            <strong>Condition {{ index + 1 }}</strong>
            <Button
                icon="pi pi-times"
                severity="danger"
                text
                rounded
                size="small"
                @click="$emit('remove')"
                v-tooltip.top="'Remove'"
            />
        </div>

        <div class="condition-fields">
            <ConditionFieldSelector
                :field="condition.field"
                :available-condition-fields="availableConditionFields"
                @update:field="updateField"
            />

            <ConditionOperatorSelector
                :operator="condition.operator"
                :operator-options="operatorOptions"
                @update:operator="update('operator', $event)"
            />

            <div class="field">
                <div class="field-label-row">
                    <label>Value *</label>
                    <SpecialValueSelector
                        :field="condition.field"
                        :available-special-values="availableSpecialValues"
                        @select="insertSpecialValue"
                    />
                    <span v-if="availableSpecialValues.length === 0"></span>
                </div>

                <ConditionValueInput
                    :field="condition.field"
                    :value="condition.value"
                    :threshold="condition.threshold"
                    :status-options="statusOptions"
                    @update:value="update('value', $event)"
                    @update:threshold="update('threshold', $event)"
                />

                <small v-if="isSpecialValue(condition.value)" class="special-value-label">
                    {{ getSpecialValueLabel(condition.value) }}
                </small>
            </div>
        </div>

        <ConditionTimeRange
            :condition-index="index"
            :use-custom-time-range="timeRange.useCustomTimeRange.value"
            :time-range="timeRange.conditionTimeRange.value"
            :time-range-unit-options="timeRange.timeRangeUnitOptions"
            :global-time-range-label="timeRange.globalTimeRangeLabel.value"
            @toggle-custom="timeRange.toggleCustomTimeRange($event)"
            @update-time-range="timeRange.updateTimeRange($event, arguments[1])"
        />
    </div>
</template>

<script setup>
import Button from 'primevue/button';
import ConditionFieldSelector from '../condition-inputs/ConditionFieldSelector.vue';
import ConditionOperatorSelector from '../condition-inputs/ConditionOperatorSelector.vue';
import ConditionValueInput from '../condition-inputs/ConditionValueInput.vue';
import SpecialValueSelector from '../condition-inputs/SpecialValueSelector.vue';
import ConditionTimeRange from '../condition-inputs/ConditionTimeRange.vue';
import { useConditionTimeRange } from '@/composables/useConditionTimeRange';
import { isSpecialValue, getSpecialValueLabel } from '@/utils/specialValues';

const props = defineProps({
    condition: {
        type: Object,
        required: true,
    },
    index: {
        type: Number,
        required: true,
    },
    availableConditionFields: {
        type: Array,
        required: true,
    },
    operatorOptions: {
        type: Array,
        required: true,
    },
    statusOptions: {
        type: Array,
        required: true,
    },
    availableSpecialValues: {
        type: Array,
        required: true,
    },
    globalTimeRange: {
        type: Object,
        default: () => ({}),
    },
});

const emit = defineEmits(['update', 'remove']);

// Initialize time range composable
const timeRange = useConditionTimeRange(props, emit);

function update(field, value) {
    emit('update', { field, value });
}

function updateField(value) {
    // Reset value and threshold when field changes
    emit('update', { field: 'field', value });
    emit('update', { field: 'value', value: null });
    // Clear threshold if field is not cpp_winning_days
    if (value !== 'cpp_winning_days') {
        emit('update', { field: 'threshold', value: null });
    }
}

function insertSpecialValue(specialValue) {
    // Store as structured value so we can apply multiplier in backend
    emit('update', { field: 'value', value: { base: specialValue, mul: 1 } });
}
</script>

<style scoped>
.condition-item {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 1rem;
    background-color: white;
}

.condition-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e5e7eb;
}

.condition-fields {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    align-items: start;
}

@media (min-width: 640px) {
    .condition-fields {
        grid-template-columns: 2fr 1fr 2.5fr;
        align-items: start;
    }
}

.condition-fields > .field {
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

.field-label-row label {
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--text-color);
}

.special-value-label {
    display: block;
    margin-top: 0.375rem;
    color: var(--text-color-secondary);
    font-size: 0.8125rem;
}
</style>
