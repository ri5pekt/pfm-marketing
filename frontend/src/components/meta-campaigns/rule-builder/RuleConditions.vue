<template>
    <div v-if="modelValue.ruleLevel" class="form-section">
        <h3 class="section-title">4. Conditions</h3>

        <div v-if="modelValue.conditionGroups.length === 0" class="empty-message">
            <p>No condition groups defined. Click "Add Group" to add one.</p>
        </div>

        <div v-else class="condition-groups-list">
            <template v-for="(group, groupIdx) in modelValue.conditionGroups" :key="group.groupId">
                <!-- OR Divider (between groups) -->
                <ConditionGroupDivider v-if="groupIdx > 0" />

                <!-- Condition Group -->
                <ConditionGroup
                    :group="group"
                    :group-index="groupIdx"
                    :can-delete="modelValue.conditionGroups.length > 1"
                    :available-condition-fields="availableConditionFields"
                    :operator-options="operatorOptions"
                    :status-options="statusOptions"
                    :available-special-values="availableSpecialValues"
                    :global-time-range="globalTimeRange"
                    @update-condition="handleGroupConditionUpdate(groupIdx, $event)"
                    @remove-condition="handleGroupConditionRemove(groupIdx, $event)"
                    @add-condition="handleGroupConditionAdd(groupIdx)"
                    @remove-group="removeGroup(groupIdx)"
                />
            </template>
        </div>

        <div class="add-group-section">
            <Button label="Add Group" icon="pi pi-plus-circle" severity="secondary" outlined @click="addGroup" />
        </div>
    </div>
</template>

<script setup>
import { computed } from "vue";
import Button from "primevue/button";
import ConditionGroup from "./ConditionGroup.vue";
import ConditionGroupDivider from "./ConditionGroupDivider.vue";
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
    { label: "ROAS", value: "roas" },
    { label: "AOV (Average Order Value)", value: "aov" },
    { label: "CTR", value: "ctr" },
    { label: "CPC", value: "cpc" },
    { label: "CPM", value: "cpm" },
    { label: "Status", value: "status" },
    { label: "Adset Status", value: "adset_status" },
    { label: "Campaign Status", value: "campaign_status" },
    { label: "Amount of Active Ads", value: "amount_of_active_ads" },
];

const adSetConditionFields = [
    { label: "Cost Per Purchase", value: "cpp" },
    { label: "Spend", value: "spend" },
    { label: "Conversions", value: "conversions" },
    { label: "ROAS", value: "roas" },
    { label: "AOV (Average Order Value)", value: "aov" },
    { label: "Daily budget", value: "daily_budget" },
    { label: "Contribution Total", value: "contribution_total" },
    { label: "Media Margin Volume", value: "media_margin_volume" },
    { label: "Status", value: "status" },
    { label: "Campaign Status", value: "campaign_status" },
    { label: "Amount of Active Ads", value: "amount_of_active_ads" },
];

const campaignConditionFields = [
    { label: "Cost Per Purchase", value: "cpp" },
    { label: "Spend", value: "spend" },
    { label: "Conversions", value: "conversions" },
    { label: "ROAS", value: "roas" },
    { label: "AOV (Average Order Value)", value: "aov" },
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

function addGroup() {
    emit("update:modelValue", {
        ...props.modelValue,
        conditionGroups: [
            ...props.modelValue.conditionGroups,
            {
                groupId: crypto.randomUUID(),
                conditions: [],
            },
        ],
    });
}

function removeGroup(groupIndex) {
    if (props.modelValue.conditionGroups.length <= 1) return;

    const newGroups = [...props.modelValue.conditionGroups];
    newGroups.splice(groupIndex, 1);

    emit("update:modelValue", {
        ...props.modelValue,
        conditionGroups: newGroups,
    });
}

function handleGroupConditionUpdate(groupIndex, { index, update }) {
    const newGroups = [...props.modelValue.conditionGroups];
    const condition = newGroups[groupIndex].conditions[index];
    newGroups[groupIndex].conditions[index] = {
        ...condition,
        [update.field]: update.value,
    };

    emit("update:modelValue", {
        ...props.modelValue,
        conditionGroups: newGroups,
    });
}

function handleGroupConditionRemove(groupIndex, conditionIndex) {
    const newGroups = [...props.modelValue.conditionGroups];
    newGroups[groupIndex].conditions.splice(conditionIndex, 1);

    emit("update:modelValue", {
        ...props.modelValue,
        conditionGroups: newGroups,
    });
}

function handleGroupConditionAdd(groupIndex) {
    const newGroups = [...props.modelValue.conditionGroups];
    newGroups[groupIndex].conditions.push({
        field: null,
        operator: null,
        value: null,
    });

    emit("update:modelValue", {
        ...props.modelValue,
        conditionGroups: newGroups,
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

.condition-groups-list {
    display: flex;
    flex-direction: column;
}

.add-group-section {
    margin-top: 1.5rem;
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
