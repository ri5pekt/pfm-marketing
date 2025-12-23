<template>
    <div v-if="modelValue.ruleLevel" class="form-section">
        <h3 class="section-title">5. Actions</h3>
        <div v-if="modelValue.actions.length === 0" class="empty-message">
            <p>No actions defined. Click "Add Action" to add one.</p>
        </div>
        <div v-else class="actions-list">
            <div v-for="(action, index) in modelValue.actions" :key="index" class="action-item">
                <div class="action-header">
                    <strong>Action {{ index + 1 }}</strong>
                    <Button
                        icon="pi pi-times"
                        severity="danger"
                        text
                        rounded
                        size="small"
                        @click="removeAction(index)"
                        v-tooltip.top="'Remove'"
                    />
                </div>
                <div class="action-fields">
                    <div class="field">
                        <label>Action Type *</label>
                        <Select
                            :modelValue="action.type"
                            @update:modelValue="updateAction(index, 'type', $event)"
                            :options="availableActionTypes"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Select action type"
                            class="w-full"
                            @change="onActionTypeChange(index)"
                        />
                    </div>
                    <!-- Set Status action fields -->
                    <div v-if="action.type === 'set_status'" class="field">
                        <label>Status *</label>
                        <Select
                            :modelValue="action.status"
                            @update:modelValue="updateAction(index, 'status', $event)"
                            :options="statusOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Select status"
                            class="w-full"
                        />
                    </div>
                    <!-- Send Notification action - no additional fields, just notification -->
                    <div v-if="action.type === 'send_notification'" class="field">
                        <small class="p-text-secondary"
                            >This action will only send a Slack notification without making any
                            changes to the item.</small
                        >
                    </div>
                    <!-- Adjust Daily Budget action fields -->
                    <template v-if="action.type === 'adjust_daily_budget'">
                        <div class="field">
                            <label>Direction *</label>
                            <Select
                                :modelValue="action.direction"
                                @update:modelValue="updateAction(index, 'direction', $event)"
                                :options="budgetDirectionOptions"
                                optionLabel="label"
                                optionValue="value"
                                placeholder="Select direction"
                                class="w-full"
                            />
                        </div>
                        <div class="field">
                            <label>Percent Value *</label>
                            <InputNumber
                                :modelValue="action.percent"
                                @update:modelValue="updateAction(index, 'percent', $event)"
                                :min="0"
                                :max="100"
                                :step="0.01"
                                placeholder="Enter percentage"
                                class="w-full"
                            />
                        </div>
                        <div class="field">
                            <label>Minimum Cap</label>
                            <InputNumber
                                :modelValue="action.minCap"
                                @update:modelValue="updateAction(index, 'minCap', $event)"
                                :min="0"
                                :step="0.01"
                                placeholder="Enter minimum cap"
                                class="w-full"
                            />
                        </div>
                        <div class="field">
                            <label>Maximum Cap</label>
                            <InputNumber
                                :modelValue="action.maxCap"
                                @update:modelValue="updateAction(index, 'maxCap', $event)"
                                :min="0"
                                :step="0.01"
                                placeholder="Enter maximum cap"
                                class="w-full"
                            />
                        </div>
                    </template>
                </div>
                <!-- Send Slack Notification checkbox - separate row at bottom -->
                <div class="action-slack-notification">
                    <div class="flex align-items-center gap-2">
                        <Checkbox
                            :modelValue="action.sendSlackNotification"
                            @update:modelValue="updateAction(index, 'sendSlackNotification', $event)"
                            :binary="true"
                            :inputId="`slack-notification-${index}`"
                            :disabled="action.type === 'send_notification'"
                        />
                        <label :for="`slack-notification-${index}`" class="slack-notification-label"
                            >Send slack notification</label
                        >
                        <small
                            v-if="action.type === 'send_notification'"
                            class="p-text-secondary ml-2"
                            >(always enabled for notification actions)</small
                        >
                    </div>
                </div>
            </div>
        </div>
        <div class="field mt-3">
            <Button
                label="Add Action"
                icon="pi pi-plus"
                severity="secondary"
                outlined
                @click="addAction"
                :disabled="!modelValue.ruleLevel"
            />
        </div>
    </div>
</template>

<script setup>
import { computed } from "vue";
import Select from "primevue/select";
import InputNumber from "primevue/inputnumber";
import Button from "primevue/button";
import Checkbox from "primevue/checkbox";

const props = defineProps({
    modelValue: {
        type: Object,
        required: true,
    },
});

const emit = defineEmits(["update:modelValue"]);

const statusOptions = [
    { label: "ACTIVE", value: "ACTIVE" },
    { label: "PAUSED", value: "PAUSED" },
    { label: "DELETED", value: "DELETED" },
];

const budgetDirectionOptions = [
    { label: "Increase", value: "increase" },
    { label: "Decrease", value: "decrease" },
];

const availableActionTypes = computed(() => {
    if (props.modelValue.ruleLevel === "ad") {
        return [
            { label: "Set Status", value: "set_status" },
            { label: "Send Notification", value: "send_notification" },
        ];
    } else if (props.modelValue.ruleLevel === "ad_set") {
        return [
            { label: "Adjust Daily Budget by Percentage", value: "adjust_daily_budget" },
            { label: "Set Status", value: "set_status" },
            { label: "Send Notification", value: "send_notification" },
        ];
    } else if (props.modelValue.ruleLevel === "campaign") {
        return [
            { label: "Set Status", value: "set_status" },
            { label: "Send Notification", value: "send_notification" },
        ];
    }
    return [];
});

function updateAction(index, field, value) {
    const newActions = [...props.modelValue.actions];
    newActions[index] = {
        ...newActions[index],
        [field]: value,
    };
    emit("update:modelValue", {
        ...props.modelValue,
        actions: newActions,
    });
}

function onActionTypeChange(index) {
    const action = props.modelValue.actions[index];
    // Reset action-specific fields when type changes
    const updatedAction = {
        ...action,
        type: action.type,
        status: null,
        direction: null,
        percent: null,
        minCap: null,
        maxCap: null,
    };
    // For send_notification, always enable slack notification
    if (action.type === "send_notification") {
        updatedAction.sendSlackNotification = true;
    } else {
        // Preserve sendSlackNotification if it exists, otherwise set to true
        if (action.sendSlackNotification === undefined) {
            updatedAction.sendSlackNotification = true;
        }
    }
    updateAction(index, "type", action.type);
    // Update all fields at once
    const newActions = [...props.modelValue.actions];
    newActions[index] = updatedAction;
    emit("update:modelValue", {
        ...props.modelValue,
        actions: newActions,
    });
}

function addAction() {
    const newActions = [
        ...props.modelValue.actions,
        {
            type: null,
            status: null,
            direction: null,
            percent: null,
            minCap: null,
            maxCap: null,
            sendSlackNotification: true, // Default to true for all actions
        },
    ];
    emit("update:modelValue", {
        ...props.modelValue,
        actions: newActions,
    });
}

function removeAction(index) {
    const newActions = [...props.modelValue.actions];
    newActions.splice(index, 1);
    emit("update:modelValue", {
        ...props.modelValue,
        actions: newActions,
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

.actions-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.action-item {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 1rem;
    background-color: white;
}

.action-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e5e7eb;
}

.action-fields {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
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

.action-slack-notification {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid #e5e7eb;
}

.slack-notification-label {
    font-size: 0.875rem;
    color: #6b7280;
    font-weight: 500;
    margin: 0;
    cursor: pointer;
}

.p-text-secondary {
    color: #6b7280;
    font-size: 0.875rem;
}

.ml-2 {
    margin-left: 0.5rem;
}

.mt-3 {
    margin-top: 1rem;
}
</style>

