import { ref } from "vue";
import { buildCronExpression, parseCronExpression } from "@/utils/cronHelpers";
import { isSpecialValue } from "@/utils/specialValues";

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

export function useRuleJsonConverter(ruleForm, formErrors, scheduleFormErrors) {
    const ruleJsonText = ref("");
    const jsonError = ref("");
    const applyingJson = ref(false);
    const isUpdatingJsonFromForm = ref(false);

    function ruleFormToJSON() {
        // Build scope filters object
        const scopeObject = {};
        ruleForm.value.scopeFilters.forEach((scope) => {
            if (scope.type === "name_contains") {
                if (Array.isArray(scope.value) && scope.value.length > 0) {
                    const filtered = scope.value.filter((v) => v && v.trim().length > 0);
                    if (filtered.length > 0) {
                        scopeObject.name_contains = filtered;
                    }
                } else if (typeof scope.value === "string" && scope.value.trim().length > 0) {
                    scopeObject.name_contains = [scope.value.trim()];
                }
            } else if (scope.type === "ids") {
                if (Array.isArray(scope.value) && scope.value.length > 0) {
                    const filtered = scope.value.filter((v) => v && v.trim().length > 0);
                    if (filtered.length > 0) {
                        scopeObject.ids = filtered;
                    }
                } else if (typeof scope.value === "string" && scope.value.trim().length > 0) {
                    const ids = parseIds(scope.value);
                    if (ids.length > 0) {
                        scopeObject.ids = ids;
                    }
                }
            } else if (scope.type === "campaign_name_contains") {
                if (Array.isArray(scope.value) && scope.value.length > 0) {
                    const filtered = scope.value.filter((v) => v && v.trim().length > 0);
                    if (filtered.length > 0) {
                        scopeObject.campaign_name_contains = filtered;
                    }
                } else if (typeof scope.value === "string" && scope.value.trim().length > 0) {
                    scopeObject.campaign_name_contains = [scope.value.trim()];
                }
            } else if (scope.type === "campaign_ids") {
                if (Array.isArray(scope.value) && scope.value.length > 0) {
                    const filtered = scope.value.filter((v) => v && v.trim().length > 0);
                    if (filtered.length > 0) {
                        scopeObject.campaign_ids = filtered;
                    }
                } else if (typeof scope.value === "string" && scope.value.trim().length > 0) {
                    const ids = parseIds(scope.value);
                    if (ids.length > 0) {
                        scopeObject.campaign_ids = ids;
                    }
                }
            }
        });

        // Build conditions JSON
        const conditionsJSON = {
            rule_level: ruleForm.value.ruleLevel,
            time_range: {
                unit: ruleForm.value.timeRangeUnit,
                amount: ruleForm.value.timeRangeUnit === "today" ? 1 : ruleForm.value.timeRangeAmount || 1,
                exclude_today: ruleForm.value.timeRangeUnit === "today" ? false : ruleForm.value.excludeToday,
            },
            conditions: ruleForm.value.conditions.map((c, idx) => {
                const conditionObj = {
                    field: c.field,
                    operator: c.operator,
                    value: c.value,
                };
                // Include threshold for CPP Winning Days
                if (c.field === "cpp_winning_days" && c.threshold !== null && c.threshold !== undefined) {
                    conditionObj.threshold = c.threshold;
                }
                // Include time_range if condition has custom time range
                // Check if time_range exists, is an object, not null, and has at least the unit property
                // Use 'in' operator to check if property exists on the object
                const hasTimeRange = c &&
                    'time_range' in c &&
                    c.time_range &&
                    typeof c.time_range === "object" &&
                    c.time_range !== null &&
                    !Array.isArray(c.time_range) &&
                    'unit' in c.time_range &&
                    c.time_range.unit;

                if (hasTimeRange) {
                    conditionObj.time_range = {
                        unit: c.time_range.unit || "days",
                        amount: c.time_range.unit === "today" ? 1 : (c.time_range.amount || 1),
                        exclude_today: c.time_range.unit === "today" ? false : (c.time_range.exclude_today !== undefined ? c.time_range.exclude_today : true),
                    };
                }
                return conditionObj;
            }),
            ...scopeObject,
        };

        // Build actions JSON
        const actionsJSON = {
            actions: ruleForm.value.actions.map((a) => {
                const action = { type: a.type };
                if (a.type === "set_status") {
                    action.status = a.status;
                } else if (a.type === "adjust_daily_budget") {
                    action.direction = a.direction;
                    action.percent = a.percent;
                    if (a.minCap !== null && a.minCap !== undefined) action.min_cap = a.minCap;
                    if (a.maxCap !== null && a.maxCap !== undefined) action.max_cap = a.maxCap;
                }
                if (a.type === "send_notification") {
                    action.send_slack_notification = true;
                } else {
                    action.send_slack_notification = a.sendSlackNotification !== undefined ? a.sendSlackNotification : true;
                }
                return action;
            }),
        };

        // Build cron expression
        const cronExpression = buildCronExpression(ruleForm.value);

        // Build exportable JSON
        const exportJSON = {
            name: ruleForm.value.name,
            description: ruleForm.value.description || null,
            enabled: ruleForm.value.enabled,
            schedule_cron: cronExpression || null,
            conditions: conditionsJSON,
            actions: actionsJSON,
        };

        return exportJSON;
    }

    function validateRuleJSON(json) {
        const errors = [];
        if (!json.name || typeof json.name !== "string" || json.name.trim() === "") {
            errors.push("'name' is required and must be a non-empty string");
        }
        if (json.enabled !== undefined && typeof json.enabled !== "boolean") {
            errors.push("'enabled' must be a boolean");
        }
        if (!json.conditions || typeof json.conditions !== "object") {
            errors.push("'conditions' is required and must be an object");
        } else {
            if (!json.conditions.rule_level) {
                errors.push("'conditions.rule_level' is required");
            }
            if (!json.conditions.time_range || typeof json.conditions.time_range !== "object") {
                errors.push("'conditions.time_range' is required and must be an object");
            } else {
                if (!json.conditions.time_range.unit) {
                    errors.push("'conditions.time_range.unit' is required");
                }
                if (json.conditions.time_range.unit !== "today") {
                    if (!json.conditions.time_range.amount || json.conditions.time_range.amount < 1) {
                        errors.push("'conditions.time_range.amount' is required and must be at least 1");
                    }
                }
            }
            if (!Array.isArray(json.conditions.conditions)) {
                errors.push("'conditions.conditions' must be an array");
            }
        }
        if (!json.actions || typeof json.actions !== "object") {
            errors.push("'actions' is required and must be an object");
        } else {
            if (!Array.isArray(json.actions.actions)) {
                errors.push("'actions.actions' must be an array");
            } else if (json.actions.actions.length === 0) {
                errors.push("'actions.actions' must contain at least one action");
            }
        }
        return errors;
    }

    function jsonToRuleForm(json) {
        // Parse cron expression
        const parsed = parseCronExpression(json.schedule_cron);
        const conditions = json.conditions || {};
        const actions = json.actions || {};

        // Parse scope filters
        const scopeFilters = [];
        if (conditions.name_contains) {
            if (Array.isArray(conditions.name_contains) && conditions.name_contains.length > 0) {
                scopeFilters.push({ type: "name_contains", value: conditions.name_contains });
            } else if (typeof conditions.name_contains === "string" && conditions.name_contains.trim().length > 0) {
                scopeFilters.push({ type: "name_contains", value: [conditions.name_contains.trim()] });
            }
        }
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
        if (conditions.campaign_name_contains) {
            if (Array.isArray(conditions.campaign_name_contains) && conditions.campaign_name_contains.length > 0) {
                scopeFilters.push({ type: "campaign_name_contains", value: conditions.campaign_name_contains });
            } else if (
                typeof conditions.campaign_name_contains === "string" &&
                conditions.campaign_name_contains.trim().length > 0
            ) {
                scopeFilters.push({ type: "campaign_name_contains", value: [conditions.campaign_name_contains.trim()] });
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

        // Parse conditions array
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
            // Include threshold for CPP Winning Days
            if (c.field === "cpp_winning_days" && c.threshold !== null && c.threshold !== undefined) {
                conditionObj.threshold = c.threshold;
            }
            // Include time_range if condition has custom time range
            if (c.time_range) {
                conditionObj.time_range = {
                    unit: c.time_range.unit,
                    amount: c.time_range.amount,
                    exclude_today: c.time_range.exclude_today !== undefined ? c.time_range.exclude_today : true,
                };
            }
            return conditionObj;
        });

        // Parse actions array
        const actionsArray = (actions.actions || []).map((action) => {
            return {
                type: action.type,
                status: action.status || null,
                direction: action.direction || null,
                percent: action.percent || null,
                minCap: action.min_cap || null,
                maxCap: action.max_cap || null,
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
            name: json.name || "",
            description: json.description || "",
            schedule_cron: json.schedule_cron || "",
            enabled: json.enabled !== undefined ? json.enabled : true,
            ruleLevel: conditions.rule_level || null,
            scopeFilters: scopeFilters,
            timeRangeUnit: timeRange.unit || null,
            timeRangeAmount: timeRange.unit === "today" ? 1 : timeRange.amount || null,
            excludeToday: timeRange.unit === "today" ? false : timeRange.exclude_today !== undefined ? timeRange.exclude_today : true,
            conditions: conditionsArray,
            actions: actionsArray,
            schedulePeriod: parsed.period || "none",
            scheduleFrequency: parsed.frequency || 1,
            scheduleTime: parsed.time || null,
            scheduleDayOfWeek: parsed.dayOfWeek !== null ? parsed.dayOfWeek : null,
            scheduleDayOfMonth: parsed.dayOfMonth !== null && parsed.dayOfMonth !== undefined ? parsed.dayOfMonth : null,
            scheduleTimezone: parsed.timezone || "UTC",
            customDailySchedule: parsed.customDailySchedule || {},
        };

        scheduleFormErrors.value = {};
        formErrors.value = {};
    }

    function updateJSONFromForm() {
        if (isUpdatingJsonFromForm.value) return;
        try {
            isUpdatingJsonFromForm.value = true;
            const json = ruleFormToJSON();
            ruleJsonText.value = JSON.stringify(json, null, 2);
            jsonError.value = "";
        } catch (error) {
            jsonError.value = `Error generating JSON: ${error.message}`;
        } finally {
            isUpdatingJsonFromForm.value = false;
        }
    }

    function validateJsonText() {
        jsonError.value = "";
        if (!ruleJsonText.value || ruleJsonText.value.trim() === "") {
            return;
        }
        try {
            JSON.parse(ruleJsonText.value);
        } catch (parseError) {
            jsonError.value = `Invalid JSON syntax: ${parseError.message}`;
        }
    }

    async function applyJsonToForm(toast) {
        applyingJson.value = true;
        jsonError.value = "";
        try {
            let json;
            try {
                json = JSON.parse(ruleJsonText.value);
            } catch (parseError) {
                jsonError.value = `Invalid JSON syntax: ${parseError.message}`;
                return;
            }
            // Validate JSON structure
            const validationErrors = validateRuleJSON(json);
            if (validationErrors.length > 0) {
                jsonError.value = `Validation errors:\n${validationErrors.join("\n")}`;
                return;
            }
            // Apply JSON to form
            jsonToRuleForm(json);
            toast.add({
                severity: "success",
                summary: "Success",
                detail: "JSON applied to form successfully",
                life: 3000,
            });
        } catch (error) {
            jsonError.value = `Error applying JSON: ${error.message}`;
            toast.add({
                severity: "error",
                summary: "Error",
                detail: `Failed to apply JSON: ${error.message}`,
                life: 5000,
            });
        } finally {
            applyingJson.value = false;
        }
    }

    return {
        ruleJsonText,
        jsonError,
        applyingJson,
        isUpdatingJsonFromForm,
        ruleFormToJSON,
        jsonToRuleForm,
        updateJSONFromForm,
        applyJsonToForm,
        validateJsonText,
        validateRuleJSON,
    };
}

