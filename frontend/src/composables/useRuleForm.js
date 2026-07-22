import { ref } from "vue";
import { parseCronExpression } from "@/utils/cronHelpers";
import { isSpecialValue } from "@/utils/specialValues";
import { appendKeywordScopesFromConditions } from "@/utils/scopeFilters";

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

export function useRuleForm() {
    // Form state
    const ruleForm = ref({
        name: "",
        description: "",
        schedule_cron: "",
        enabled: true,
        ruleLevel: null,
        scopeFilters: [],
        timeRangeUnit: null,
        timeRangeAmount: null,
        excludeToday: true,
        conditionGroups: [
            {
                groupId: crypto.randomUUID(),
                conditions: [],
            },
        ],
        actions: [],
        schedulePeriod: null,
        scheduleFrequency: 1,
        scheduleTime: null,
        scheduleDayOfWeek: null,
        scheduleDayOfMonth: null,
        scheduleTimezone: "UTC",
        customDailySchedule: {},
    });

    const formErrors = ref({});
    const scheduleFormErrors = ref({});

    function resetForm() {
        ruleForm.value = {
            name: "",
            description: "",
            schedule_cron: "",
            enabled: true,
            ruleLevel: null,
            scopeFilters: [],
            timeRangeUnit: null,
            timeRangeAmount: null,
            excludeToday: true,
            conditionGroups: [
                {
                    groupId: crypto.randomUUID(),
                    conditions: [],
                },
            ],
            actions: [],
            schedulePeriod: null,
            scheduleFrequency: 1,
            scheduleTime: null,
            scheduleDayOfWeek: null,
            scheduleDayOfMonth: null,
            scheduleTimezone: "UTC",
            customDailySchedule: {},
        };
        formErrors.value = {};
        scheduleFormErrors.value = {};
    }

    function updateRuleForm(newForm) {
        // Directly update the reactive form object to preserve reactivity
        // Update each property individually to ensure Vue's reactivity system tracks changes
        Object.keys(newForm).forEach((key) => {
            if (Array.isArray(newForm[key])) {
                // For arrays (conditions, actions, scopeFilters), replace the entire array
                ruleForm.value[key] = newForm[key];
            } else if (typeof newForm[key] === "object" && newForm[key] !== null) {
                // For objects, merge them
                ruleForm.value[key] = {
                    ...ruleForm.value[key],
                    ...newForm[key],
                };
            } else {
                // For primitives, assign directly
                ruleForm.value[key] = newForm[key];
            }
        });
    }

    function initializeFormFromRule(rule) {
        // Parse cron expression
        const parsed = parseCronExpression(rule.schedule_cron);
        const conditions = rule.conditions || {};
        const actions = rule.actions || {};

        // Parse scope filters
        const scopeFilters = [];
        appendKeywordScopesFromConditions(scopeFilters, conditions);
        if (conditions.ids) {
            if (Array.isArray(conditions.ids) && conditions.ids.length > 0) {
                scopeFilters.push({ type: "ids", value: conditions.ids });
            } else if (typeof conditions.ids === "string" && conditions.ids.trim().length > 0) {
                const ids = parseIds(conditions.ids);
                if (ids.length > 0) {
                    scopeFilters.push({ type: "ids", value: ids });
                }
            }
        }
        if (conditions.campaign_ids) {
            if (Array.isArray(conditions.campaign_ids) && conditions.campaign_ids.length > 0) {
                scopeFilters.push({ type: "campaign_ids", value: conditions.campaign_ids });
            } else if (typeof conditions.campaign_ids === "string" && conditions.campaign_ids.trim().length > 0) {
                const ids = parseIds(conditions.campaign_ids);
                if (ids.length > 0) {
                    scopeFilters.push({ type: "campaign_ids", value: ids });
                }
            }
        }

        // Parse condition groups (handle both new and old formats)
        let conditionGroups = [];

        // New format: condition_groups
        if (conditions.condition_groups) {
            conditionGroups = conditions.condition_groups.map((group) => ({
                groupId: group.group_id || crypto.randomUUID(),
                conditions: (group.conditions || []).map((c) => {
                    let value = c.value;
                    // Normalize legacy special values (string) to structured form
                    if (typeof value === "string" && isSpecialValue(value)) {
                        value = { base: value, mul: 1 };
                    }
                    // Normalize structured values missing multiplier
                    if (
                        typeof value === "object" &&
                        value &&
                        typeof value.base === "string" &&
                        value.mul === undefined
                    ) {
                        value = { ...value, mul: 1 };
                    }
                    const conditionObj = {
                        field: c.field,
                        operator: c.operator,
                        value,
                    };
                    // Include time_range if condition has custom time range
                    if (
                        c.time_range &&
                        typeof c.time_range === "object" &&
                        c.time_range !== null &&
                        c.time_range.unit
                    ) {
                        conditionObj.time_range = {
                            unit: c.time_range.unit,
                            amount: c.time_range.amount,
                            exclude_today: c.time_range.exclude_today !== undefined ? c.time_range.exclude_today : true,
                        };
                    }
                    return conditionObj;
                }),
            }));
        }
        // Old format: flat conditions array (backward compatibility)
        else if (conditions.conditions) {
            const conditionsArray = (conditions.conditions || []).map((c) => {
                let value = c.value;
                // Normalize legacy special values (string) to structured form
                if (typeof value === "string" && isSpecialValue(value)) {
                    value = { base: value, mul: 1 };
                }
                // Normalize structured values missing multiplier
                if (typeof value === "object" && value && typeof value.base === "string" && value.mul === undefined) {
                    value = { ...value, mul: 1 };
                }
                const conditionObj = {
                    field: c.field,
                    operator: c.operator,
                    value,
                };
                // Include time_range if condition has custom time range
                if (c.time_range && typeof c.time_range === "object" && c.time_range !== null && c.time_range.unit) {
                    conditionObj.time_range = {
                        unit: c.time_range.unit,
                        amount: c.time_range.amount,
                        exclude_today: c.time_range.exclude_today !== undefined ? c.time_range.exclude_today : true,
                    };
                }
                return conditionObj;
            });
            // Wrap in single group for backward compatibility
            conditionGroups = [
                {
                    groupId: crypto.randomUUID(),
                    conditions: conditionsArray,
                },
            ];
        }
        // Default: empty group
        else {
            conditionGroups = [
                {
                    groupId: crypto.randomUUID(),
                    conditions: [],
                },
            ];
        }

        // Parse actions array
        const actionsArray = (actions.actions || []).map((action) => {
            return {
                type: action.type,
                status: action.status || null,
                direction: action.direction || null,
                percent: action.percent || null,
                minCap: action.min_cap || null,
                maxCap: action.max_cap || null,
                text: action.text || null,
                sendSlackNotification:
                    action.type === "send_notification"
                        ? true
                        : action.send_slack_notification !== undefined
                          ? action.send_slack_notification
                          : true,
            };
        });

        // Parse time range
        const timeRange = conditions.time_range || {};

        ruleForm.value = {
            name: rule.name,
            description: rule.description || "",
            schedule_cron: rule.schedule_cron,
            enabled: rule.enabled,
            ruleLevel: conditions.rule_level || null,
            scopeFilters: scopeFilters,
            timeRangeUnit: timeRange.unit || null,
            timeRangeAmount: timeRange.unit === "today" ? 1 : timeRange.amount || null,
            excludeToday:
                timeRange.unit === "today"
                    ? false
                    : timeRange.exclude_today !== undefined
                      ? timeRange.exclude_today
                      : true,
            conditionGroups: conditionGroups,
            actions: actionsArray,
            schedulePeriod: parsed.period || "none",
            scheduleFrequency: parsed.frequency || 1,
            scheduleTime: parsed.time || null,
            scheduleDayOfWeek: parsed.dayOfWeek !== null ? parsed.dayOfWeek : null,
            scheduleDayOfMonth:
                parsed.dayOfMonth !== null && parsed.dayOfMonth !== undefined ? parsed.dayOfMonth : null,
            scheduleTimezone: parsed.timezone || "UTC",
            customDailySchedule: parsed.customDailySchedule || {},
        };

        scheduleFormErrors.value = {};
        formErrors.value = {};
    }

    function addConditionGroup() {
        ruleForm.value.conditionGroups.push({
            groupId: crypto.randomUUID(),
            conditions: [],
        });
    }

    function removeConditionGroup(groupId) {
        // Keep at least one group
        if (ruleForm.value.conditionGroups.length <= 1) {
            return;
        }
        const index = ruleForm.value.conditionGroups.findIndex((g) => g.groupId === groupId);
        if (index !== -1) {
            ruleForm.value.conditionGroups.splice(index, 1);
        }
    }

    function addConditionToGroup(groupId) {
        const group = ruleForm.value.conditionGroups.find((g) => g.groupId === groupId);
        if (group) {
            group.conditions.push({
                field: null,
                operator: null,
                value: null,
            });
        }
    }

    function removeConditionFromGroup(groupId, conditionIndex) {
        const group = ruleForm.value.conditionGroups.find((g) => g.groupId === groupId);
        if (group && group.conditions.length > conditionIndex) {
            group.conditions.splice(conditionIndex, 1);
        }
    }

    return {
        ruleForm,
        formErrors,
        scheduleFormErrors,
        resetForm,
        updateRuleForm,
        initializeFormFromRule,
        addConditionGroup,
        removeConditionGroup,
        addConditionToGroup,
        removeConditionFromGroup,
    };
}
