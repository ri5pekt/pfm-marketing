<template>
    <div class="compact-value-input">
        <div class="value-input-row">
            <!-- Main value input based on comparison type -->
            <div class="value-input-main">
                <!-- Status selector (auto-shown when field is status) -->
                <StatusValueInput
                    v-if="isStatusField"
                    :value="value"
                    :status-options="statusOptions"
                    @update:value="$emit('update:value', $event)"
                />

                <!-- Metric selector (shows dropdown of special values) -->
                <Select
                    v-else-if="comparisonType === 'metric'"
                    :modelValue="metricBase"
                    @update:modelValue="updateMetricBase"
                    :options="availableSpecialValues"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select metric"
                    class="w-full"
                />

                <!-- Regular value input (numeric or text) -->
                <NumericValueInput
                    v-else-if="isNumericField"
                    :value="value"
                    @update:value="$emit('update:value', $event)"
                />

                <TextValueInput
                    v-else
                    :value="value"
                    :placeholder="placeholder"
                    @update:value="$emit('update:value', $event)"
                />
            </div>

            <!-- Multiplier (shown for metric comparison type) -->
            <div v-if="comparisonType === 'metric' && !isStatusField" class="multiplier">
                <span class="multiplier-prefix">×</span>
                <InputNumber
                    :modelValue="metricMultiplier"
                    @update:modelValue="updateMetricMultiplier"
                    :min="0"
                    :step="0.01"
                    :minFractionDigits="0"
                    :maxFractionDigits="6"
                    placeholder="1"
                    class="multiplier-input"
                    inputMode="decimal"
                    :useGrouping="false"
                />
            </div>

            <!-- Comparison type selector -->
            <SelectButton
                v-if="!isStatusField"
                :modelValue="comparisonType"
                @update:modelValue="updateComparisonType"
                :options="comparisonTypeOptions"
                optionLabel="label"
                optionValue="value"
                aria-labelledby="basic"
                class="comparison-type-selector"
            />
        </div>
    </div>
</template>

<script setup>
import { computed } from "vue";
import Select from "primevue/select";
import SelectButton from "primevue/selectbutton";
import InputNumber from "primevue/inputnumber";
import StatusValueInput from "./StatusValueInput.vue";
import NumericValueInput from "./NumericValueInput.vue";
import TextValueInput from "./TextValueInput.vue";
import { isFieldStatus, isFieldNumeric } from "@/utils/conditionFieldConfig";
import {
    getValuePlaceholder,
    isSpecialValue,
    getSpecialBase,
    getSpecialMul,
    getSpecialValueLabel,
} from "@/utils/specialValues";

const props = defineProps({
    field: {
        type: [String, null],
        required: false,
        default: null,
    },
    value: {
        type: [String, Number, Object, null],
        default: null,
    },
    statusOptions: {
        type: Array,
        default: () => [],
    },
    availableSpecialValues: {
        type: Array,
        default: () => [],
    },
});

const emit = defineEmits(["update:value"]);

// Comparison type options
const comparisonTypeOptions = computed(() => {
    const options = [{ label: "Value", value: "value" }];

    // Only show Metric option if special values are available
    if (props.availableSpecialValues.length > 0 && !isStatusField.value) {
        options.push({ label: "Metric", value: "metric" });
    }

    return options;
});

// Determine if field is status or numeric
const isStatusField = computed(() => isFieldStatus(props.field));
const isNumericField = computed(() => isFieldNumeric(props.field));

// Get placeholder text
const placeholder = computed(() => getValuePlaceholder(props.field));

// Determine current comparison type based on value
const comparisonType = computed(() => {
    if (isStatusField.value) return "value"; // Status fields always use value mode
    if (isSpecialValue(props.value)) return "metric";
    return "value";
});

// Extract metric base and multiplier
const metricBase = computed(() => {
    if (isSpecialValue(props.value)) {
        return getSpecialBase(props.value);
    }
    return null;
});

const metricMultiplier = computed(() => {
    if (isSpecialValue(props.value)) {
        return getSpecialMul(props.value);
    }
    return 1;
});

// Get metric label
function getMetricLabel(base) {
    return getSpecialValueLabel({ base, mul: 1 });
}

// Update comparison type
function updateComparisonType(type) {
    if (type === "metric") {
        // Switch to metric mode - set first available special value
        if (props.availableSpecialValues.length > 0) {
            emit("update:value", {
                base: props.availableSpecialValues[0].value,
                mul: 1,
            });
        }
    } else {
        // Switch to value mode - reset to null
        emit("update:value", null);
    }
}

// Update metric base
function updateMetricBase(base) {
    emit("update:value", {
        base: base || "",
        mul: metricMultiplier.value,
    });
}

// Update metric multiplier
function updateMetricMultiplier(mul) {
    const safeMul = mul === null || mul === undefined || mul === "" ? 1 : Number(mul);
    emit("update:value", {
        base: metricBase.value || "",
        mul: safeMul,
    });
}
</script>

<style scoped>
.compact-value-input {
    width: 100%;
}

.value-input-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.value-input-main {
    flex: 1;
    min-width: 0;
}

.multiplier {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    flex-shrink: 0;
}

.multiplier-prefix {
    font-weight: 600;
    color: var(--text-color-secondary);
}

.multiplier-input {
    width: 50px;
    max-width: 50px;
    min-width: 50px;
    flex-shrink: 0;
}

.multiplier-input :deep(input) {
    width: 50px !important;
    max-width: 50px !important;
    min-width: 50px !important;
    text-align: center;
}

.comparison-type-selector {
    flex-shrink: 0;
}
</style>
