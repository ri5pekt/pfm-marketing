<template>
    <Dialog
        :visible="modelValue"
        @update:visible="$emit('update:modelValue', $event)"
        :header="editingRule ? 'Edit Rule' : 'Create Rule'"
        :modal="true"
        :style="{ maxWidth: '900px', width: '90vw', maxHeight: '90vh' }"
        class="rule-builder-dialog"
    >
        <TabView v-model:activeIndex="activeTabIndex">
            <TabPanel header="Form Editor">
                <div class="form-content">
                    <RuleBasicInfo :modelValue="ruleForm" :errors="formErrors" @update:modelValue="updateRuleForm" />
                    <RuleLevelAndScope
                        :modelValue="ruleForm"
                        :errors="formErrors"
                        :availableScopeTypes="availableScopeTypes"
                        @update:modelValue="updateRuleForm"
                        @openAddScopeDialog="showAddScopeDialog = true"
                        @clearScopeError="formErrors.scopeFilters = ''"
                        @ruleLevelChanged="onRuleLevelChange"
                    />
                    <RuleTimeRange :modelValue="ruleForm" :errors="formErrors" @update:modelValue="updateRuleForm" />
                    <RuleConditions :modelValue="ruleForm" @update:modelValue="updateRuleForm" />
                    <RuleActions :modelValue="ruleForm" @update:modelValue="updateRuleForm" />
                    <RuleSchedule
                        :modelValue="ruleForm"
                        :errors="scheduleFormErrors"
                        @update:modelValue="updateRuleForm"
                        @schedulePeriodChanged="onSchedulePeriodChange"
                        @validateTime="validateTime"
                    />
                </div>
            </TabPanel>
            <TabPanel header="JSON Editor">
                <RuleJsonEditor
                    :modelValue="ruleJsonText"
                    :jsonError="jsonError"
                    :applyingJson="applyingJson"
                    @update:modelValue="ruleJsonText = $event"
                    @input="validateJsonText"
                    @applyJson="handleApplyJson"
                    @copyJson="copyJsonToClipboard"
                />
            </TabPanel>
        </TabView>

        <AddScopeDialog
            :modelValue="showAddScopeDialog"
            :availableScopeTypes="availableScopeTypes"
            @update:modelValue="showAddScopeDialog = $event"
            @add="addScopeFilter"
        />

        <template #footer>
            <Button label="Cancel" severity="secondary" @click="handleCancel" />
            <Button :label="editingRule ? 'Update' : 'Create'" @click="handleSave" :loading="saving" />
        </template>
    </Dialog>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useToast } from "primevue/usetoast";
import Dialog from "primevue/dialog";
import TabView from "primevue/tabview";
import TabPanel from "primevue/tabpanel";
import Button from "primevue/button";
import RuleBasicInfo from "../rule-builder/RuleBasicInfo.vue";
import RuleLevelAndScope from "../rule-builder/RuleLevelAndScope.vue";
import RuleTimeRange from "../rule-builder/RuleTimeRange.vue";
import RuleConditions from "../rule-builder/RuleConditions.vue";
import RuleActions from "../rule-builder/RuleActions.vue";
import RuleSchedule from "../rule-builder/RuleSchedule.vue";
import RuleJsonEditor from "../rule-builder/RuleJsonEditor.vue";
import AddScopeDialog from "../rule-builder/AddScopeDialog.vue";
import { buildCronExpression } from "@/utils/cronHelpers";
import { scopeTypeOptions } from "@/utils/specialValues";
import { useRuleForm } from "@/composables/useRuleForm";
import { useRuleJsonConverter } from "@/composables/useRuleJsonConverter";
import { useRuleSchedule } from "@/composables/useRuleSchedule";

const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false,
    },
    editingRule: {
        type: Object,
        default: null,
    },
    selectedAccountId: {
        type: [String, Number],
        default: null,
    },
});

const emit = defineEmits(["update:modelValue", "save", "cancel"]);

const toast = useToast();

// Use composables
const { ruleForm, formErrors, scheduleFormErrors, resetForm, updateRuleForm, initializeFormFromRule } = useRuleForm();
const {
    ruleJsonText,
    jsonError,
    applyingJson,
    isUpdatingJsonFromForm,
    ruleFormToJSON,
    jsonToRuleForm,
    updateJSONFromForm,
    applyJsonToForm,
    validateJsonText,
} = useRuleJsonConverter(ruleForm, formErrors, scheduleFormErrors);
const { onSchedulePeriodChange, validateTime, validateSchedule } = useRuleSchedule(ruleForm, scheduleFormErrors);

// Local state
const showAddScopeDialog = ref(false);
const activeTabIndex = ref(0);
const saving = ref(false);

// Computed: Available scope types
const availableScopeTypes = computed(() => {
    const addedTypes = ruleForm.value.scopeFilters.map((s) => s.type);
    let filteredOptions = scopeTypeOptions;
    if (ruleForm.value.ruleLevel === "campaign") {
        filteredOptions = scopeTypeOptions.filter(
            (opt) => opt.value !== "campaign_name_contains" && opt.value !== "campaign_ids"
        );
    }
    return filteredOptions.filter((opt) => !addedTypes.includes(opt.value));
});

// Initialize form when dialog opens or editingRule changes
watch(
    () => [props.modelValue, props.editingRule],
    ([isOpen, rule]) => {
        if (isOpen) {
            if (rule) {
                initializeFormFromRule(rule);
            } else {
                resetForm();
            }
            activeTabIndex.value = 0;
            ruleJsonText.value = "";
            jsonError.value = "";
            updateJSONFromForm();
        }
    },
    { immediate: true }
);

// Watch form changes and update JSON
watch(
    () => ruleForm.value,
    () => {
        if (!isUpdatingJsonFromForm.value) {
            updateJSONFromForm();
        }
    },
    { deep: true }
);

function onRuleLevelChange() {
    // Clear conditions and actions when rule level changes
    ruleForm.value.conditions = [];
    ruleForm.value.actions = [];
}

function addScopeFilter(scopeType) {
    if (!scopeType) return;

    const newScope = {
        type: scopeType,
        value:
            scopeType === "name_contains" ||
            scopeType === "ids" ||
            scopeType === "campaign_name_contains" ||
            scopeType === "campaign_ids"
                ? []
                : "",
    };
    ruleForm.value.scopeFilters.push(newScope);
    showAddScopeDialog.value = false;
    updateJSONFromForm();
}

async function copyJsonToClipboard() {
    try {
        await navigator.clipboard.writeText(ruleJsonText.value);
        toast.add({
            severity: "success",
            summary: "Success",
            detail: "JSON copied to clipboard",
            life: 3000,
        });
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: "Failed to copy JSON to clipboard",
            life: 5000,
        });
    }
}

async function handleApplyJson() {
    await applyJsonToForm(toast);
    activeTabIndex.value = 0;
}

function handleCancel() {
    emit("cancel");
    emit("update:modelValue", false);
}

function validateForm() {
    formErrors.value = {};
    if (!ruleForm.value.name || ruleForm.value.name.trim() === "") {
        formErrors.value.name = "Rule name is required";
    }
    if (!ruleForm.value.ruleLevel) {
        formErrors.value.ruleLevel = "Rule level is required";
    }
    if (!ruleForm.value.scopeFilters || ruleForm.value.scopeFilters.length === 0) {
        formErrors.value.scopeFilters = "At least one scope filter is required";
    } else {
        const invalidScopes = [];
        ruleForm.value.scopeFilters.forEach((scope, idx) => {
            if (scope.type === "name_contains" || scope.type === "campaign_name_contains") {
                if (!scope.value || !Array.isArray(scope.value) || scope.value.length === 0) {
                    invalidScopes.push({
                        index: idx,
                        type: scope.type,
                        label: "Name contains",
                        reason: "value is empty",
                    });
                } else {
                    const validValues = scope.value.filter((v) => v && typeof v === "string" && v.trim().length > 0);
                    if (validValues.length === 0) {
                        invalidScopes.push({
                            index: idx,
                            type: scope.type,
                            label: "Name contains",
                            reason: "all values are empty",
                        });
                    }
                }
            } else if (scope.type === "ids" || scope.type === "campaign_ids") {
                if (Array.isArray(scope.value)) {
                    const filtered = scope.value.filter((v) => v && String(v).trim().length > 0);
                    if (filtered.length === 0) {
                        invalidScopes.push({
                            index: idx,
                            type: scope.type,
                            label: scope.type === "ids" ? "IDs" : "Campaign IDs",
                            reason: "value is empty",
                        });
                    }
                } else {
                    // Helper to parse IDs from textarea (comma or newline separated) or return array as-is
                    function parseIds(text) {
                        if (Array.isArray(text)) {
                            return text.filter((id) => id && String(id).trim().length > 0);
                        }
                        if (typeof text === "string") {
                            if (!text || !text.trim()) return [];
                            return text
                                .split(/[,\n]/)
                                .map((id) => id.trim())
                                .filter((id) => id.length > 0);
                        }
                        return [];
                    }
                    const ids = parseIds(scope.value);
                    if (ids.length === 0) {
                        invalidScopes.push({
                            index: idx,
                            type: scope.type,
                            label: scope.type === "ids" ? "IDs" : "Campaign IDs",
                            reason: "no valid IDs parsed",
                        });
                    }
                }
            }
        });
        if (invalidScopes.length > 0) {
            const nameContainsIssue = invalidScopes.find(
                (s) => s.type === "name_contains" || s.type === "campaign_name_contains"
            );
            if (nameContainsIssue) {
                formErrors.value.scopeFilters = `The "Name contains" filter requires at least one keyword. Please type a keyword and press Enter to add it.`;
            } else {
                const labels = invalidScopes.map((s) => s.label).join(", ");
                formErrors.value.scopeFilters = `The following scope filter(s) are missing values: ${labels}. Please fill in all required fields.`;
            }
        }
    }
    if (!ruleForm.value.timeRangeUnit) {
        formErrors.value.timeRangeUnit = "Time unit is required";
    } else if (ruleForm.value.timeRangeUnit !== "today") {
        if (!ruleForm.value.timeRangeAmount || ruleForm.value.timeRangeAmount < 1) {
            formErrors.value.timeRangeAmount = "Time amount is required and must be at least 1";
        }
    }
    // Validate conditions
    if (!ruleForm.value.conditions || ruleForm.value.conditions.length === 0) {
        formErrors.value.conditions = "At least one condition is required";
    } else {
        const invalidConditions = [];
        ruleForm.value.conditions.forEach((condition, idx) => {
            if (!condition.field) {
                invalidConditions.push({ index: idx, field: "field", message: "Field is required" });
            }
            if (!condition.operator) {
                invalidConditions.push({ index: idx, field: "operator", message: "Operator is required" });
            }
            if (condition.value === null || condition.value === undefined || condition.value === "") {
                invalidConditions.push({ index: idx, field: "value", message: "Value is required" });
            }
            // Validate threshold for CPP Winning Days
            if (condition.field === "cpp_winning_days") {
                if (condition.threshold === null || condition.threshold === undefined || condition.threshold === "") {
                    invalidConditions.push({
                        index: idx,
                        field: "threshold",
                        message: "Threshold is required for CPP Winning Days",
                    });
                } else if (condition.threshold < 0) {
                    invalidConditions.push({
                        index: idx,
                        field: "threshold",
                        message: "Threshold must be greater than or equal to 0",
                    });
                }
            }
        });
        if (invalidConditions.length > 0) {
            const messages = invalidConditions.map((c) => `Condition ${c.index + 1}: ${c.message}`).join("; ");
            formErrors.value.conditions = messages;
        }
    }
    if (!validateSchedule()) {
        // Errors already in scheduleFormErrors
    }
    return Object.keys(formErrors.value).length === 0 && Object.keys(scheduleFormErrors.value).length === 0;
}

async function handleSave() {
    if (!props.selectedAccountId) {
        toast.add({
            severity: "warn",
            summary: "Warning",
            detail: "Please select an ad account first",
            life: 3000,
        });
        return;
    }

    if (!validateForm()) {
        const errors = [];
        if (formErrors.value.name) errors.push(`Name: ${formErrors.value.name}`);
        if (formErrors.value.ruleLevel) errors.push(`Rule Level: ${formErrors.value.ruleLevel}`);
        if (formErrors.value.scopeFilters) errors.push(`Scope Filters: ${formErrors.value.scopeFilters}`);
        if (formErrors.value.timeRangeUnit) errors.push(`Time Unit: ${formErrors.value.timeRangeUnit}`);
        if (formErrors.value.timeRangeAmount) errors.push(`Time Amount: ${formErrors.value.timeRangeAmount}`);
        if (formErrors.value.conditions) errors.push(`Conditions: ${formErrors.value.conditions}`);
        if (scheduleFormErrors.value.period) errors.push(`Schedule Period: ${scheduleFormErrors.value.period}`);
        if (scheduleFormErrors.value.frequency)
            errors.push(`Schedule Frequency: ${scheduleFormErrors.value.frequency}`);
        if (scheduleFormErrors.value.time) errors.push(`Schedule Time: ${scheduleFormErrors.value.time}`);
        if (scheduleFormErrors.value.dayOfWeek) errors.push(`Day of Week: ${scheduleFormErrors.value.dayOfWeek}`);
        if (scheduleFormErrors.value.dayOfMonth) errors.push(`Day of Month: ${scheduleFormErrors.value.dayOfMonth}`);
        const errorMessage = errors.length > 0 ? errors.join("; ") : "Please fix all form errors";
        toast.add({
            severity: "warn",
            summary: "Validation Error",
            detail: errorMessage,
            life: 6000,
        });
        return;
    }

    const cronExpression = buildCronExpression(ruleForm.value);
    if (ruleForm.value.schedulePeriod && ruleForm.value.schedulePeriod !== "none" && !cronExpression) {
        toast.add({
            severity: "warn",
            summary: "Validation Error",
            detail: "Invalid schedule configuration",
            life: 3000,
        });
        return;
    }

    saving.value = true;
    try {
        const ruleData = ruleFormToJSON();
        ruleData.ad_account_id = props.selectedAccountId;
        if (props.editingRule) {
            ruleData.id = props.editingRule.id;
        }
        emit("save", ruleData);
        emit("update:modelValue", false);
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: error.message || "Failed to save rule",
            life: 5000,
        });
    } finally {
        saving.value = false;
    }
}
</script>

<style scoped>
.rule-builder-dialog :deep(.p-dialog-content) {
    max-height: calc(90vh - 150px);
    overflow-y: auto;
    overflow-x: hidden;
}

.rule-builder-dialog :deep(.p-dialog-footer) {
    padding-top: 1rem;
}

.form-content {
    padding: 0.5rem 0;
}
</style>
