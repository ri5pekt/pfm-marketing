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
            <div class="field">
                <div class="field-label-row">
                    <label>Field *</label>
                    <span></span>
                </div>
                <Select
                    :modelValue="condition.field"
                    @update:modelValue="updateField($event)"
                    :options="availableConditionFields"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select field"
                    class="w-full"
                />
            </div>
            <div class="field">
                <div class="field-label-row">
                    <label>Operator *</label>
                    <span></span>
                </div>
                <Select
                    :modelValue="condition.operator"
                    @update:modelValue="update('operator', $event)"
                    :options="operatorOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select operator"
                    class="w-full"
                />
            </div>
            <div class="field">
                <div class="field-label-row">
                    <label>Value *</label>
                    <!-- Special Value Button -->
                    <Button
                        v-if="availableSpecialValues.length > 0"
                        label="Add Special Value"
                        severity="secondary"
                        outlined
                        @click="(event) => toggleSpecialValueMenu(event)"
                        type="button"
                        class="special-value-button-inline"
                        :disabled="!condition.field"
                        size="small"
                    />
                    <span v-else></span>
                </div>
                <div class="value-input-wrapper">
                    <Select
                        v-if="condition.field === 'status' || condition.field === 'campaign_status'"
                        :modelValue="condition.value"
                        @update:modelValue="update('value', $event)"
                        :options="statusOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="Select status"
                        class="w-full value-input"
                    />

                    <!-- Special value selected: show base token + multiplier -->
                    <div
                        v-else-if="isSpecialValue(condition.value)"
                        class="special-value-row"
                    >
                        <InputText
                            class="value-input special-value"
                            :modelValue="getSpecialBase(condition.value)"
                            @update:modelValue="(v) => setSpecialBase(v)"
                            placeholder="__daily_budget__"
                        />
                        <div class="multiplier">
                            <span class="multiplier-prefix">×</span>
                            <InputNumber
                                :modelValue="getSpecialMul(condition.value)"
                                @update:modelValue="(v) => setSpecialMul(v)"
                                :min="0"
                                :step="0.01"
                                :minFractionDigits="0"
                                :maxFractionDigits="6"
                                placeholder="1"
                                class="multiplier-input"
                            />
                        </div>
                    </div>

                    <!-- CPP Winning Days: requires threshold input -->
                    <div v-else-if="condition.field === 'cpp_winning_days'" class="cpp-winning-days-inputs">
                        <div class="value-input">
                            <label class="threshold-label">Winning Days Count *</label>
                            <InputNumber
                                :modelValue="condition.value"
                                @update:modelValue="update('value', $event)"
                                :min="0"
                                :step="1"
                                :minFractionDigits="0"
                                :maxFractionDigits="0"
                                placeholder="Enter number of days"
                                class="w-full"
                            />
                        </div>
                        <div class="threshold-input">
                            <label class="threshold-label">Threshold (CPP) *</label>
                            <InputNumber
                                :modelValue="condition.threshold"
                                @update:modelValue="update('threshold', $event)"
                                :step="0.01"
                                :min="0"
                                :minFractionDigits="0"
                                :maxFractionDigits="6"
                                placeholder="Enter CPP threshold"
                                class="w-full"
                            />
                        </div>
                        <small class="p-text-secondary">
                            Counts days where CPP was below the threshold
                        </small>
                    </div>
                    <InputNumber
                        v-else-if="isNumericField(condition.field)"
                        :modelValue="condition.value"
                        @update:modelValue="update('value', $event)"
                        :step="0.01"
                        :minFractionDigits="0"
                        :maxFractionDigits="6"
                        placeholder="Enter value"
                        class="w-full value-input"
                    />
                    <InputText
                        v-else
                        :modelValue="condition.value"
                        @update:modelValue="update('value', $event)"
                        :placeholder="getValuePlaceholder(condition.field)"
                        class="w-full value-input"
                    />
                </div>
                <!-- Show current special value label if one is selected -->
                <small v-if="isSpecialValue(condition.value)" class="special-value-label">
                    {{ getSpecialValueLabel(condition.value) }}
                </small>

                <!-- Special Value Dropdown Menu -->
                <OverlayPanel ref="specialValueMenuRef" :dismissable="true">
                    <div class="special-values-menu">
                        <div class="special-values-title">Special Values</div>
                        <div
                            v-for="(special, idx) in availableSpecialValues"
                            :key="idx"
                            class="special-value-item"
                            @click="insertSpecialValue(special.value)"
                        >
                            <div class="special-value-item-label">{{ special.label }}</div>
                            <div class="special-value-item-code">{{ special.value }}</div>
                            <div class="special-value-item-desc">
                                {{ special.description }}
                            </div>
                        </div>
                    </div>
                </OverlayPanel>
            </div>
        </div>

        <!-- Time Range Section -->
        <div class="condition-time-range">
            <div class="time-range-header">
                <div class="flex align-items-center gap-2">
                    <InputSwitch
                        :modelValue="useCustomTimeRange"
                        @update:modelValue="toggleCustomTimeRange($event)"
                        :inputId="`useCustomTimeRange-${index}`"
                    />
                    <label :for="`useCustomTimeRange-${index}`" class="field-label">Use custom time range</label>
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
                            :modelValue="conditionTimeRange.unit"
                            @update:modelValue="updateTimeRange('unit', $event)"
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
                            :modelValue="conditionTimeRange.amount"
                            @update:modelValue="updateTimeRange('amount', $event)"
                            :min="1"
                            placeholder="Enter amount"
                            class="w-full"
                            :disabled="conditionTimeRange.unit === 'today'"
                        />
                        <small v-if="conditionTimeRange.unit === 'today'" class="p-text-secondary">
                            (Automatically set to 1 day for today only)
                        </small>
                    </div>
                </div>
                <div class="field">
                    <div class="flex align-items-center gap-2">
                        <InputSwitch
                            :modelValue="conditionTimeRange.exclude_today"
                            @update:modelValue="updateTimeRange('exclude_today', $event)"
                            :inputId="`conditionExcludeToday-${index}`"
                            :disabled="
                                conditionTimeRange.unit === 'minutes' ||
                                conditionTimeRange.unit === 'hours' ||
                                conditionTimeRange.unit === 'today'
                            "
                        />
                        <label :for="`conditionExcludeToday-${index}`" class="field-label">Exclude today</label>
                    </div>
                    <small
                        class="p-text-secondary"
                        v-if="conditionTimeRange.unit === 'minutes' || conditionTimeRange.unit === 'hours'"
                    >
                        (No effect for minutes or hours)
                    </small>
                    <small class="p-text-secondary" v-if="conditionTimeRange.unit === 'today'">
                        (Disabled for today only)
                    </small>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from "vue";
import Select from "primevue/select";
import InputText from "primevue/inputtext";
import InputNumber from "primevue/inputnumber";
import Button from "primevue/button";
import InputSwitch from "primevue/inputswitch";
import OverlayPanel from "primevue/overlaypanel";
import {
    isSpecialValue,
    getSpecialBase,
    getSpecialMul,
    getSpecialValueLabel,
    isNumericField,
    getValuePlaceholder,
} from "@/utils/specialValues";

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

const specialValueMenuRef = ref(null);

const timeRangeUnitOptions = [
    { label: "Minutes", value: "minutes" },
    { label: "Hours", value: "hours" },
    { label: "Days", value: "days" },
    { label: "Today only", value: "today" },
];

// Check if condition has custom time range
// Use a more specific check to ensure reactivity is isolated to this condition
const useCustomTimeRange = computed({
    get: () => {
        // Explicitly check this condition's time_range property
        const condition = props.condition;
        return !!(condition && condition.time_range && typeof condition.time_range === "object" && condition.time_range !== null);
    },
    set: (value) => {
        if (value) {
            // Initialize with global time range if available, or defaults
            const defaultTimeRange = {
                unit: props.globalTimeRange?.timeRangeUnit || "days",
                amount: props.globalTimeRange?.timeRangeAmount || 7,
                exclude_today: props.globalTimeRange?.excludeToday !== undefined ? props.globalTimeRange.excludeToday : true,
            };
            emit("update", { field: "time_range", value: defaultTimeRange });
        } else {
            // Remove custom time range (will use global)
            emit("update", { field: "time_range", value: null });
        }
    },
});

const conditionTimeRange = computed({
    get: () => {
        if (props.condition.time_range) {
            return {
                unit: props.condition.time_range.unit || "days",
                amount: props.condition.time_range.amount || 7,
                exclude_today: props.condition.time_range.exclude_today !== undefined ? props.condition.time_range.exclude_today : true,
            };
        }
        return {
            unit: "days",
            amount: 7,
            exclude_today: true,
        };
    },
    set: (value) => {
        emit("update", { field: "time_range", value });
    },
});

const globalTimeRangeLabel = computed(() => {
    if (!props.globalTimeRange || !props.globalTimeRange.timeRangeUnit) {
        return "Not set";
    }
    const unit = props.globalTimeRange.timeRangeUnit;
    const amount = props.globalTimeRange.timeRangeAmount || 1;
    const excludeToday = props.globalTimeRange.excludeToday;

    if (unit === "today") {
        return "Today only";
    }

    const unitLabel = unit === "minutes" ? "min" : unit === "hours" ? "hr" : "day";
    const excludeText = excludeToday ? " (excl. today)" : "";
    return `${amount} ${unitLabel}${amount !== 1 ? "s" : ""}${excludeText}`;
});

function toggleCustomTimeRange(value) {
    useCustomTimeRange.value = value;
}

function updateTimeRange(field, value) {
    const newTimeRange = {
        ...conditionTimeRange.value,
        [field]: value,
    };
    // Handle special case for "today"
    if (field === "unit" && value === "today") {
        newTimeRange.amount = 1;
        newTimeRange.exclude_today = false;
    }
    emit("update", { field: "time_range", value: newTimeRange });
}

function update(field, value) {
    emit("update", { field, value });
}

function updateField(value) {
    // Reset value and threshold when field changes
    emit("update", { field: "field", value });
    emit("update", { field: "value", value: null });
    // Clear threshold if field is not cpp_winning_days
    if (value !== "cpp_winning_days") {
        emit("update", { field: "threshold", value: null });
    }
}

function toggleSpecialValueMenu(event) {
    if (specialValueMenuRef.value) {
        specialValueMenuRef.value.toggle(event);
    }
}

function insertSpecialValue(specialValue) {
    // Store as structured value so we can apply multiplier in backend
    emit("update", { field: "value", value: { base: specialValue, mul: 1 } });
    // Close the overlay if it exists
    if (specialValueMenuRef.value) {
        specialValueMenuRef.value.hide();
    }
}

function setSpecialBase(base) {
    const baseStr = base === null || base === undefined ? "" : String(base);

    // Normalize legacy string -> object
    if (typeof props.condition.value === "string" && isSpecialValue(props.condition.value)) {
        emit("update", { field: "value", value: { base: baseStr, mul: 1 } });
        return;
    }

    if (typeof props.condition.value === "object" && props.condition.value) {
        emit("update", {
            field: "value",
            value: {
                ...props.condition.value,
                base: baseStr,
                mul: props.condition.value.mul !== undefined ? props.condition.value.mul : 1,
            },
        });
    } else {
        emit("update", { field: "value", value: { base: baseStr, mul: 1 } });
    }
}

function setSpecialMul(mul) {
    const safeMul = mul === null || mul === undefined || mul === "" ? 1 : Number(mul);

    // Normalize legacy string -> object
    if (typeof props.condition.value === "string" && isSpecialValue(props.condition.value)) {
        emit("update", { field: "value", value: { base: props.condition.value, mul: safeMul } });
        return;
    }

    if (typeof props.condition.value === "object" && props.condition.value) {
        emit("update", {
            field: "value",
            value: {
                ...props.condition.value,
                mul: safeMul,
            },
        });
    }
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

.condition-fields > .field > * {
    min-width: 0;
}

.value-input-wrapper {
    width: 100%;
    min-width: 0;
    display: flex;
    flex-direction: column;
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

.field-label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    min-height: 2rem;
    height: 2rem;
}

.field-label-row label {
    margin-bottom: 0;
    line-height: 2rem;
}

.special-value-button-inline {
    margin-left: auto;
}

.special-value-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    width: 100%;
    flex-wrap: nowrap;
    min-width: 0;
}

.special-value-row .value-input.special-value {
    flex: 1 1 auto;
    min-width: 0;
}

.special-value-row :deep(.p-inputtext) {
    min-width: 0;
    width: 100%;
}

.special-value-row .multiplier {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    white-space: nowrap;
    flex: 0 0 auto;
}

.special-value-row .multiplier-prefix {
    font-weight: 600;
    opacity: 0.8;
    flex-shrink: 0;
}

.special-value-row .multiplier-input {
    flex: 0 0 80px;
    min-width: 80px;
}

.special-value-row .multiplier :deep(.p-inputnumber),
.special-value-row .multiplier :deep(.p-inputnumber input) {
    width: 100%;
    min-width: 80px;
}


.special-value-label {
    color: #6b7280;
    font-size: 0.875rem;
    margin-top: 0.25rem;
    display: block;
}

.special-values-menu {
    min-width: 300px;
    max-width: 400px;
}

.special-values-title {
    font-weight: 600;
    padding: 0.5rem;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 0.5rem;
}

.special-value-item {
    padding: 0.75rem;
    cursor: pointer;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.special-value-item:hover {
    background-color: #f3f4f6;
}

.special-value-item-label {
    font-weight: 500;
    color: #1f2937;
    margin-bottom: 0.25rem;
}

.special-value-item-code {
    font-family: monospace;
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 0.25rem;
}

.special-value-item-desc {
    font-size: 0.75rem;
    color: #9ca3af;
}

.condition-time-range {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
}

.time-range-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}

.time-range-fields {
    margin-top: 0.75rem;
    padding: 0.75rem;
    background-color: #f9fafb;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
}

.fields-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}

.field-half {
    flex: 1;
    margin-bottom: 0;
}

.p-text-secondary {
    color: #6b7280;
    font-size: 0.875rem;
}

.cpp-winning-days-inputs {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.cpp-winning-days-inputs .threshold-input,
.cpp-winning-days-inputs .value-input {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.threshold-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
}
</style>

