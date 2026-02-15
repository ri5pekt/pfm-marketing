/**
 * Field type definitions and operator configurations for condition fields
 */

// Field type categories
export const FIELD_TYPES = {
    STATUS: "status",
    NUMERIC: "numeric",
    SPECIAL: "special",
    TEXT: "text",
};

// Operator sets
export const OPERATORS = {
    COMPARISON: [
        { label: ">", value: "gt" },
        { label: ">=", value: "gte" },
        { label: "<", value: "lt" },
        { label: "<=", value: "lte" },
        { label: "=", value: "eq" },
        { label: "!=", value: "neq" },
    ],
    EQUALITY: [
        { label: "=", value: "eq" },
        { label: "!=", value: "neq" },
    ],
    STRING: [
        { label: "Contains", value: "contains" },
        { label: "Does not contain", value: "not_contains" },
        { label: "=", value: "eq" },
        { label: "!=", value: "neq" },
    ],
};

// Field configurations mapping field names to their types and properties
export const FIELD_CONFIG = {
    status: {
        type: FIELD_TYPES.STATUS,
        operators: OPERATORS.EQUALITY,
        supportsSpecialValues: false,
    },
    campaign_status: {
        type: FIELD_TYPES.STATUS,
        operators: OPERATORS.EQUALITY,
        supportsSpecialValues: false,
    },
    spend: {
        type: FIELD_TYPES.NUMERIC,
        operators: OPERATORS.COMPARISON,
        supportsSpecialValues: true,
    },
    cpp: {
        type: FIELD_TYPES.NUMERIC,
        operators: OPERATORS.COMPARISON,
        supportsSpecialValues: true,
    },
    purchase_count: {
        type: FIELD_TYPES.NUMERIC,
        operators: OPERATORS.COMPARISON,
        supportsSpecialValues: false,
    },
    purchase_value: {
        type: FIELD_TYPES.NUMERIC,
        operators: OPERATORS.COMPARISON,
        supportsSpecialValues: false,
    },
    roas: {
        type: FIELD_TYPES.NUMERIC,
        operators: OPERATORS.COMPARISON,
        supportsSpecialValues: false,
    },
    ctr: {
        type: FIELD_TYPES.NUMERIC,
        operators: OPERATORS.COMPARISON,
        supportsSpecialValues: false,
    },
    conversion_rate: {
        type: FIELD_TYPES.NUMERIC,
        operators: OPERATORS.COMPARISON,
        supportsSpecialValues: false,
    },
    cpp_winning_days: {
        type: FIELD_TYPES.SPECIAL, // Special handling for cpp_winning_days
        operators: OPERATORS.COMPARISON,
        supportsSpecialValues: false,
        requiresThreshold: true,
    },
    name: {
        type: FIELD_TYPES.TEXT,
        operators: OPERATORS.STRING,
        supportsSpecialValues: false,
    },
};

/**
 * Get field configuration
 */
export function getFieldConfig(fieldName) {
    return (
        FIELD_CONFIG[fieldName] || {
            type: FIELD_TYPES.TEXT,
            operators: OPERATORS.STRING,
            supportsSpecialValues: false,
        }
    );
}

/**
 * Get operators for a field
 */
export function getOperatorsForField(fieldName) {
    const config = getFieldConfig(fieldName);
    return config.operators;
}

/**
 * Check if field supports special values
 */
export function fieldSupportsSpecialValues(fieldName) {
    const config = getFieldConfig(fieldName);
    return config.supportsSpecialValues === true;
}

/**
 * Check if field is numeric
 */
export function isFieldNumeric(fieldName) {
    const config = getFieldConfig(fieldName);
    return config.type === FIELD_TYPES.NUMERIC;
}

/**
 * Check if field is status type
 */
export function isFieldStatus(fieldName) {
    const config = getFieldConfig(fieldName);
    return config.type === FIELD_TYPES.STATUS;
}

/**
 * Check if field requires threshold (like cpp_winning_days)
 */
export function fieldRequiresThreshold(fieldName) {
    const config = getFieldConfig(fieldName);
    return config.requiresThreshold === true;
}

/**
 * Determine value input component type based on field
 */
export function getValueInputType(fieldName, value) {
    if (isFieldStatus(fieldName)) {
        return "status";
    }

    if (fieldRequiresThreshold(fieldName)) {
        return "cpp-winning-days";
    }

    // Check if value is a special value (object with base and mul)
    if (typeof value === "object" && value !== null && "base" in value) {
        return "special";
    }

    if (isFieldNumeric(fieldName)) {
        return "numeric";
    }

    return "text";
}
