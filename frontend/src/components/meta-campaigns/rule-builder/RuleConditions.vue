<template>
    <div v-if="modelValue.ruleLevel" class="form-section">
        <h3 class="section-title">4. Conditions</h3>
        <div v-if="modelValue.conditions.length === 0" class="empty-message">
            <p>No conditions defined. Click "Add Condition" to add one.</p>
        </div>
        <div v-else class="conditions-list">
            <ConditionItem
                v-for="(condition, index) in modelValue.conditions"
                :key="index"
                :condition="condition"
                :index="index"
                :availableConditionFields="availableConditionFields"
                :operatorOptions="operatorOptions"
                :statusOptions="statusOptions"
                :availableSpecialValues="availableSpecialValues"
                :globalTimeRange="globalTimeRange"
                @update="handleConditionUpdate(index, $event)"
                @remove="removeCondition(index)"
            />
        </div>
        <div class="field mt-3">
            <Button
                label="Add Condition"
                icon="pi pi-plus"
                severity="secondary"
                outlined
                @click="addCondition"
                :disabled="!modelValue.ruleLevel"
            />
        </div>
    </div>
</template>

<script setup>
import { computed } from "vue";
import Button from "primevue/button";
import ConditionItem from "./ConditionItem.vue";
import { getAvailableSpecialValues } from "@/utils/specialValues";

const props = defineProps({
    modelValue: {
        type: Object,
        required: true,
    },
});

const emit = defineEmits(["update:modelValue"]);

const operatorOptions = [
    { label: ">", value: ">" },
    { label: ">=", value: ">=" },
    { label: "<", value: "<" },
    { label: "<=", value: "<=" },
    { label: "=", value: "=" },
    { label: "!=", value: "!=" },
];

const statusOptions = [
    { label: "ACTIVE", value: "ACTIVE" },
    { label: "PAUSED", value: "PAUSED" },
    { label: "DELETED", value: "DELETED" },
];

const adConditionFields = [
    { label: "Cost Per Purchase", value: "cpp" },
    { label: "Spend", value: "spend" },
    { label: "Conversions", value: "conversions" },
    { label: "CTR", value: "ctr" },
    { label: "CPC", value: "cpc" },
    { label: "CPM", value: "cpm" },
    { label: "CPP Winning Days", value: "cpp_winning_days" },
    { label: "Status", value: "status" },
    { label: "Campaign Status", value: "campaign_status" },
    { label: "Amount of Active Ads", value: "amount_of_active_ads" },
];

const adSetConditionFields = [
    { label: "Cost Per Purchase", value: "cpp" },
    { label: "Spend", value: "spend" },
    { label: "Conversions", value: "conversions" },
    { label: "ROAS", value: "roas" },
    { label: "Daily budget", value: "daily_budget" },
    { label: "Media Margin Volume", value: "media_margin_volume" },
    { label: "CPP Winning Days", value: "cpp_winning_days" },
    { label: "Status", value: "status" },
    { label: "Campaign Status", value: "campaign_status" },
    { label: "Amount of Active Ads", value: "amount_of_active_ads" },
];

const campaignConditionFields = [
    { label: "Cost Per Purchase", value: "cpp" },
    { label: "Spend", value: "spend" },
    { label: "Conversions", value: "conversions" },
    { label: "ROAS", value: "roas" },
    { label: "CPP Winning Days", value: "cpp_winning_days" },
    { label: "Status", value: "status" },
    { label: "Amount of Active Ads", value: "amount_of_active_ads" },
];

const availableConditionFields = computed(() => {
    if (props.modelValue.ruleLevel === "ad") {
        return adConditionFields;
    } else if (props.modelValue.ruleLevel === "ad_set") {
        return adSetConditionFields;
    } else if (props.modelValue.ruleLevel === "campaign") {
        return campaignConditionFields;
    }
    return [];
});

const availableSpecialValues = computed(() => {
    return getAvailableSpecialValues(props.modelValue.ruleLevel);
});

const globalTimeRange = computed(() => {
    return {
        timeRangeUnit: props.modelValue.timeRangeUnit,
        timeRangeAmount: props.modelValue.timeRangeAmount,
        excludeToday: props.modelValue.excludeToday,
    };
});

function handleConditionUpdate(index, { field, value }) {
    const newConditions = [...props.modelValue.conditions];
    // Ensure we preserve all existing properties of the condition
    const existingCondition = newConditions[index] || {};
    newConditions[index] = {
        ...existingCondition,
        [field]: value,
    };

    emit("update:modelValue", {
        ...props.modelValue,
        conditions: newConditions,
    });
}

function addCondition() {
    const newConditions = [
        ...props.modelValue.conditions,
        {
            field: null,
            operator: null,
            value: null,
        },
    ];
    emit("update:modelValue", {
        ...props.modelValue,
        conditions: newConditions,
    });
}

function removeCondition(index) {
    const newConditions = [...props.modelValue.conditions];
    newConditions.splice(index, 1);
    emit("update:modelValue", {
        ...props.modelValue,
        conditions: newConditions,
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

.empty-message {
    padding: 1rem;
    background-color: #f3f4f6;
    border-radius: 6px;
    color: #6b7280;
    text-align: center;
    margin-bottom: 1rem;
}

.conditions-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.field {
    margin-bottom: 1rem;
}

.field:last-child {
    margin-bottom: 0;
}

.mt-3 {
    margin-top: 1rem;
}
</style>
