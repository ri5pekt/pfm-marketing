<template>
    <div class="rule-editor-view">
        <div class="editor-content">
            <Tabs v-model:value="activeTabIndex">
                <TabList>
                    <Tab :value="0">Form Editor</Tab>
                    <Tab :value="1">JSON Editor</Tab>
                </TabList>
                <TabPanels>
                    <TabPanel :value="0">
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
                    <TabPanel :value="1">
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
                </TabPanels>
            </Tabs>

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
import { ref, computed, watch, onMounted, inject, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";
import Tabs from "primevue/tabs";
import TabList from "primevue/tablist";
import Tab from "primevue/tab";
import TabPanels from "primevue/tabpanels";
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

// Inject page header from AppShell
const pageHeader = inject('pageHeader', null);

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

// Update page header
function updatePageHeader() {
    if (pageHeader) {
        pageHeader.title = isEditMode.value ? (ruleForm.value.name || 'Edit Rule') : 'New Rule';
        pageHeader.showBackButton = true;
        pageHeader.onBack = goBack;
    }
}

// Load rule data if editing
onMounted(async () => {
    // Set initial page header
    updatePageHeader();
    
    if (isEditMode.value && ruleId.value) {
        // Edit mode: Load rule and get account ID from rule data
        loading.value = true;
        try {
            const rule = await getRule(ruleId.value);
            selectedAccountId.value = rule.ad_account_id;
            initializeFormFromRule(rule);
            updateJSONFromForm();
            // Update header with loaded rule name
            updatePageHeader();
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
        // Create mode: Get account ID from route query or localStorage
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

        resetForm();
        updateJSONFromForm();
    }
});

// Clear page header on unmount
onUnmounted(() => {
    if (pageHeader) {
        pageHeader.title = '';
        pageHeader.subtitle = '';
        pageHeader.showBackButton = false;
        pageHeader.onBack = () => {};
    }
});

// Watch for rule name changes to update header
watch(() => ruleForm.value.name, () => {
    if (isEditMode.value) {
        updatePageHeader();
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
    ruleForm.value.conditionGroups = [{
        groupId: crypto.randomUUID(),
        conditions: []
    }];
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
    // Validate condition groups
    if (!ruleForm.value.conditionGroups || ruleForm.value.conditionGroups.length === 0) {
        formErrors.value.conditions = "At least one condition group is required";
    } else {
        const invalidConditions = [];
        let totalConditions = 0;
        
        ruleForm.value.conditionGroups.forEach((group, groupIdx) => {
            if (!group.conditions || group.conditions.length === 0) {
                invalidConditions.push({ 
                    groupIndex: groupIdx, 
                    conditionIndex: null, 
                    message: `Group ${groupIdx + 1} has no conditions` 
                });
            } else {
                totalConditions += group.conditions.length;
                group.conditions.forEach((condition, condIdx) => {
                    if (!condition.field) {
                        invalidConditions.push({ 
                            groupIndex: groupIdx, 
                            conditionIndex: condIdx, 
                            field: "field", 
                            message: "Field is required" 
                        });
                    }
                    if (!condition.operator) {
                        invalidConditions.push({ 
                            groupIndex: groupIdx, 
                            conditionIndex: condIdx, 
                            field: "operator", 
                            message: "Operator is required" 
                        });
                    }
                    if (condition.value === null || condition.value === undefined || condition.value === "") {
                        invalidConditions.push({ 
                            groupIndex: groupIdx, 
                            conditionIndex: condIdx, 
                            field: "value", 
                            message: "Value is required" 
                        });
                    }
                    
                    // Validate custom time range if enabled
                    if (condition.time_range && typeof condition.time_range === "object") {
                        if (!condition.time_range.unit) {
                            invalidConditions.push({ 
                                groupIndex: groupIdx, 
                                conditionIndex: condIdx, 
                                field: "time_range", 
                                message: "Custom time range unit is required" 
                            });
                        }
                        if (condition.time_range.unit !== "today") {
                            if (!condition.time_range.amount || condition.time_range.amount < 1 || isNaN(condition.time_range.amount)) {
                                invalidConditions.push({ 
                                    groupIndex: groupIdx, 
                                    conditionIndex: condIdx, 
                                    field: "time_range", 
                                    message: "Custom time range amount is required and must be a valid number" 
                                });
                            }
                        }
                    }
                });
            }
        });
        
        if (totalConditions === 0) {
            formErrors.value.conditions = "At least one condition is required";
        } else if (invalidConditions.length > 0) {
            const messages = invalidConditions.map((c) => {
                if (c.conditionIndex !== null) {
                    return `Group ${c.groupIndex + 1}, Condition ${c.conditionIndex + 1}: ${c.message}`;
                } else {
                    return c.message;
                }
            }).join("; ");
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
            // Navigate back with success message
            router.push({ 
                name: "meta-campaigns", 
                query: { ruleUpdated: "true", ruleName: ruleForm.value.name } 
            });
        } else {
            await createRule(ruleData);
            // Navigate back with success message
            router.push({ 
                name: "meta-campaigns", 
                query: { ruleCreated: "true", ruleName: ruleForm.value.name } 
            });
        }
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

    .editor-footer {
        padding: 1rem;
    }
}
</style>
