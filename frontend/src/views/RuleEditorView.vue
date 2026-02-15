<template>
    <div class="rule-editor-view">
        <div class="editor-header">
            <Button icon="pi pi-arrow-left" text @click="goBack" class="back-button" />
            <h1>{{ isEditMode ? "Edit Rule" : "Create Rule" }}</h1>
        </div>

        <div class="editor-content">
            <TabView v-model:activeIndex="activeTabIndex">
                <TabPanel header="Form Editor">
                    <div class="form-content">
                        <RuleBasicInfo
                            :modelValue="ruleForm"
                            :errors="formErrors"
                            @update:modelValue="updateRuleForm"
                        />
                        <RuleLevelAndScope
                            :modelValue="ruleForm"
                            :errors="formErrors"
                            :availableScopeTypes="availableScopeTypes"
                            @update:modelValue="updateRuleForm"
                            @openAddScopeDialog="showAddScopeDialog = true"
                            @clearScopeError="formErrors.scopeFilters = ''"
                            @ruleLevelChanged="onRuleLevelChange"
                        />
                        <RuleTimeRange
                            :modelValue="ruleForm"
                            :errors="formErrors"
                            @update:modelValue="updateRuleForm"
                        />
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
        </div>

        <div class="editor-footer">
            <Button label="Cancel" severity="secondary" @click="goBack" />
            <Button :label="isEditMode ? 'Update' : 'Create'" @click="handleSave" :loading="saving" />
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";
import TabView from "primevue/tabview";
import TabPanel from "primevue/tabpanel";
import Button from "primevue/button";
import RuleBasicInfo from "@/components/meta-campaigns/rule-builder/RuleBasicInfo.vue";
import RuleLevelAndScope from "@/components/meta-campaigns/rule-builder/RuleLevelAndScope.vue";
import RuleTimeRange from "@/components/meta-campaigns/rule-builder/RuleTimeRange.vue";
import RuleConditions from "@/components/meta-campaigns/rule-builder/RuleConditions.vue";
import RuleActions from "@/components/meta-campaigns/rule-builder/RuleActions.vue";
import RuleSchedule from "@/components/meta-campaigns/rule-builder/RuleSchedule.vue";
import RuleJsonEditor from "@/components/meta-campaigns/rule-builder/RuleJsonEditor.vue";
import AddScopeDialog from "@/components/meta-campaigns/rule-builder/AddScopeDialog.vue";
import { buildCronExpression } from "@/utils/cronHelpers";
import { scopeTypeOptions } from "@/utils/specialValues";
import { useRuleForm } from "@/composables/useRuleForm";
import { useRuleJsonConverter } from "@/composables/useRuleJsonConverter";
import { useRuleSchedule } from "@/composables/useRuleSchedule";
import { getRule, createRule, updateRule } from "@/api/metaCampaignsApi";

const route = useRoute();
const router = useRouter();
const toast = useToast();

// Determine mode from route
const isEditMode = computed(() => route.name === "rule-edit");
const ruleId = computed(() => route.params.id);

// Get selected account ID from route query or localStorage
const selectedAccountId = ref(null);

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
const loading = ref(false);

// Computed: Available scope types
const availableScopeTypes = computed(() => {
    const addedTypes = ruleForm.value.scopeFilters.map((s) => s.type);
    let filteredOptions = scopeTypeOptions;
    if (ruleForm.value.ruleLevel === "campaign") {
        filteredOptions = scopeTypeOptions.filter(
            (opt) => opt.value !== "campaign_name_contains" && opt.value !== "campaign_ids",
        );
    }
    return filteredOptions.filter((opt) => !addedTypes.includes(opt.value));
});

// Load rule data if editing
onMounted(async () => {
    // Get account ID from route query or localStorage
    selectedAccountId.value = route.query.accountId || localStorage.getItem("pfm_selected_account_id");

    if (!selectedAccountId.value) {
        toast.add({
            severity: "warn",
            summary: "Warning",
            detail: "No ad account selected",
            life: 3000,
        });
        goBack();
        return;
    }

    if (isEditMode.value && ruleId.value) {
        loading.value = true;
        try {
            const rule = await getRule(ruleId.value);
            initializeFormFromRule(rule);
            updateJSONFromForm();
        } catch (error) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to load rule",
                life: 5000,
            });
            goBack();
        } finally {
            loading.value = false;
        }
    } else {
        resetForm();
        updateJSONFromForm();
    }
});

// Watch form changes and update JSON
watch(
    () => ruleForm.value,
    () => {
        if (!isUpdatingJsonFromForm.value) {
            updateJSONFromForm();
        }
    },
    { deep: true },
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

function goBack() {
    router.push({ name: "meta-campaigns" });
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
                (s) => s.type === "name_contains" || s.type === "campaign_name_contains",
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
    if (!selectedAccountId.value) {
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
        ruleData.ad_account_id = selectedAccountId.value;

        if (isEditMode.value) {
            await updateRule(ruleId.value, ruleData);
            toast.add({
                severity: "success",
                summary: "Success",
                detail: "Rule updated successfully",
                life: 3000,
            });
        } else {
            await createRule(ruleData);
            toast.add({
                severity: "success",
                summary: "Success",
                detail: "Rule created successfully",
                life: 3000,
            });
        }

        goBack();
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: error.message || `Failed to ${isEditMode.value ? "update" : "create"} rule`,
            life: 5000,
        });
    } finally {
        saving.value = false;
    }
}
</script>

<style scoped>
.rule-editor-view {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    background-color: var(--surface-ground);
}

.editor-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.5rem 2rem;
    background-color: var(--surface-card);
    border-bottom: 1px solid var(--surface-border);
    position: sticky;
    top: 0;
    z-index: 100;
}

.editor-header h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
}

.back-button {
    font-size: 1.25rem;
}

.editor-content {
    flex: 1;
    padding: 2rem;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
}

.form-content {
    padding: 0.5rem 0;
}

.editor-footer {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    padding: 1.5rem 2rem;
    background-color: var(--surface-card);
    border-top: 1px solid var(--surface-border);
    position: sticky;
    bottom: 0;
    z-index: 100;
}

/* Adjust for mobile */
@media (max-width: 768px) {
    .editor-content {
        padding: 1rem;
    }

    .editor-header,
    .editor-footer {
        padding: 1rem;
    }
}
</style>
