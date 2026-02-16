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

            <CompactConditionValueInput
                :field="condition.field"
                :value="condition.value"
                :status-options="statusOptions"
                :available-special-values="availableSpecialValues"
                @update:value="update('value', $event)"
            />
        </div>

        <ConditionTimeRange
            :condition-index="index"
            :use-custom-time-range="timeRange.useCustomTimeRange.value"
            :time-range="timeRange.conditionTimeRange.value"
            :time-range-unit-options="timeRange.timeRangeUnitOptions"
            :global-time-range-label="timeRange.globalTimeRangeLabel.value"
            @toggle-custom="timeRange.toggleCustomTimeRange($event)"
            @update-time-range="(field, value) => timeRange.updateTimeRange(field, value)"
        />
    </div>
</template>

<script setup>
import Button from "primevue/button";
import ConditionFieldSelector from "../condition-inputs/ConditionFieldSelector.vue";
import ConditionOperatorSelector from "../condition-inputs/ConditionOperatorSelector.vue";
import CompactConditionValueInput from "../condition-inputs/CompactConditionValueInput.vue";
import ConditionTimeRange from "../condition-inputs/ConditionTimeRange.vue";
import { useConditionTimeRange } from "@/composables/useConditionTimeRange";

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

const emit = defineEmits(["update", "remove"]);

// Initialize time range composable
const timeRange = useConditionTimeRange(props, emit);

function update(field, value) {
    emit("update", { field, value });
}

function updateField(value) {
    // Reset value when field changes
    emit("update", { field: "field", value });
    emit("update", { field: "value", value: null });
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

</style>
