/**
 * Special values utilities for rule conditions
 */

export const specialValues = {
    ad: [
        { label: "Current Daily Budget", value: "__daily_budget__", description: "Adset's current daily budget" },
        { label: "Current Spend", value: "__current_spend__", description: "Current spend in time range" },
    ],
    ad_set: [
        { label: "Current Daily Budget", value: "__daily_budget__", description: "Adset's current daily budget" },
        { label: "Lifetime Budget", value: "__lifetime_budget__", description: "Adset's lifetime budget" },
        { label: "Current Spend", value: "__current_spend__", description: "Current spend in time range" },
    ],
    campaign: [
        { label: "Current Spend", value: "__current_spend__", description: "Current spend in time range" }
    ],
};

/**
 * Check if a value is a special value (supports legacy string and structured { base, mul } object)
 */
export function isSpecialValue(value) {
    if (!value) return false;
    const base =
        typeof value === "string"
            ? value
            : typeof value === "object" && typeof value.base === "string"
            ? value.base
            : null;
    return !!base && String(base).startsWith("__") && String(base).endsWith("__");
}

/**
 * Get the base special value from a value (handles both string and object formats)
 */
export function getSpecialBase(value) {
    if (!value) return "";
    return typeof value === "string" ? value : value.base || "";
}

/**
 * Get the multiplier from a special value
 */
export function getSpecialMul(value) {
    if (!value) return 1;
    if (typeof value === "object" && value.mul !== undefined && value.mul !== null) return Number(value.mul);
    return 1;
}

/**
 * Set the base special value on a condition
 */
export function setSpecialBase(condition, base) {
    const baseStr = base === null || base === undefined ? "" : String(base);

    // Normalize legacy string -> object
    if (typeof condition.value === "string" && isSpecialValue(condition.value)) {
        condition.value = { base: baseStr, mul: 1 };
        return;
    }

    if (typeof condition.value === "object" && condition.value) {
        condition.value.base = baseStr;
        if (condition.value.mul === undefined) condition.value.mul = 1;
    } else {
        condition.value = { base: baseStr, mul: 1 };
    }
}

/**
 * Set the multiplier on a special value condition
 */
export function setSpecialMul(condition, mul) {
    const safeMul = mul === null || mul === undefined || mul === "" ? 1 : Number(mul);

    // Normalize legacy string -> object
    if (typeof condition.value === "string" && isSpecialValue(condition.value)) {
        condition.value = { base: condition.value, mul: safeMul };
        return;
    }

    if (typeof condition.value === "object" && condition.value) {
        condition.value.mul = safeMul;
    }
}

/**
 * Get the label for a special value
 */
export function getSpecialValueLabel(value) {
    if (!isSpecialValue(value)) return "";
    const base = getSpecialBase(value);
    const allValues = [...specialValues.ad, ...specialValues.ad_set, ...specialValues.campaign];
    const found = allValues.find((sv) => sv.value === base);
    return found ? found.label : base;
}

/**
 * Get available special values for a rule level
 */
export function getAvailableSpecialValues(ruleLevel) {
    return specialValues[ruleLevel] || [];
}

/**
 * Check if a field is numeric
 */
export function isNumericField(field) {
    const numericFields = [
        "cpp",
        "spend",
        "conversions",
        "ctr",
        "cpc",
        "cpm",
        "roas",
        "daily_budget",
        "media_margin_volume",
        "cpp_winning_days",
        "amount_of_active_ads",
    ];
    return numericFields.includes(field);
}

/**
 * Get placeholder text for a condition field
 */
export function getValuePlaceholder(field) {
    if (field === "status" || field === "campaign_status") {
        return "ACTIVE or PAUSED";
    } else if (field === "name_contains") {
        return "Enter text to match";
    }
    return "Enter value";
}

/**
 * Scope type options for rule filters
 */
export const scopeTypeOptions = [
    { label: "Name contains", value: "name_contains" },
    { label: "IDs", value: "ids" },
    { label: "Campaign Name contains", value: "campaign_name_contains" },
    { label: "Campaign IDs", value: "campaign_ids" },
];

