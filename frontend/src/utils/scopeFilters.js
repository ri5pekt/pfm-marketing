/** Scope types that may appear more than once (AND across instances). */
export const MULTI_ALLOWED_SCOPE_TYPES = new Set([
    "name_contains",
    "campaign_name_contains",
    "campaign_name_doesnt_contain",
]);

const KEYWORD_SCOPE_TYPES = [
    "name_contains",
    "campaign_name_contains",
    "campaign_name_doesnt_contain",
];

/**
 * Detect nested keyword groups: [["a"], ["b"]] vs flat ["a", "b"].
 */
function isNestedKeywordGroups(value) {
    return Array.isArray(value) && value.length > 0 && Array.isArray(value[0]);
}

/**
 * Expand a stored keyword filter into one or more UI scope entries.
 * Flat list -> one scope (existing rules). Nested groups -> one scope per group.
 */
export function expandKeywordScopeToFilters(type, value) {
    if (value == null) return [];

    if (typeof value === "string") {
        const trimmed = value.trim();
        return trimmed ? [{ type, value: [trimmed] }] : [];
    }

    if (!Array.isArray(value) || value.length === 0) return [];

    if (isNestedKeywordGroups(value)) {
        return value
            .map((group) => {
                if (!Array.isArray(group)) return null;
                const filtered = group.filter((v) => v && String(v).trim().length > 0).map((v) => String(v).trim());
                return filtered.length > 0 ? { type, value: filtered } : null;
            })
            .filter(Boolean);
    }

    const filtered = value.filter((v) => v && String(v).trim().length > 0).map((v) => String(v).trim());
    return filtered.length > 0 ? [{ type, value: filtered }] : [];
}

/**
 * Collect keyword scopes of the same type into a stored value.
 * One group -> flat list (preserves existing rule format).
 * Multiple groups -> nested list (AND across groups).
 */
export function collectKeywordScopeValue(scopeFilters, type) {
    const groups = [];
    for (const scope of scopeFilters) {
        if (scope.type !== type) continue;
        if (Array.isArray(scope.value) && scope.value.length > 0) {
            const filtered = scope.value.filter((v) => v && String(v).trim().length > 0).map((v) => String(v).trim());
            if (filtered.length > 0) groups.push(filtered);
        } else if (typeof scope.value === "string" && scope.value.trim().length > 0) {
            groups.push([scope.value.trim()]);
        }
    }
    if (groups.length === 0) return undefined;
    if (groups.length === 1) return groups[0];
    return groups;
}

/**
 * Append all keyword-type scopes from conditions into scopeFilters array.
 */
export function appendKeywordScopesFromConditions(scopeFilters, conditions) {
    for (const type of KEYWORD_SCOPE_TYPES) {
        if (conditions[type]) {
            scopeFilters.push(...expandKeywordScopeToFilters(type, conditions[type]));
        }
    }
}
