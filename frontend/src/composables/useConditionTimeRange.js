import { computed } from "vue";

/**
 * Composable for managing condition-specific time range
 */
export function useConditionTimeRange(props, emit) {
    const timeRangeUnitOptions = [
        { label: "Minutes", value: "minutes" },
        { label: "Hours", value: "hours" },
        { label: "Days", value: "days" },
        { label: "Today only", value: "today" },
    ];

    // Check if condition has custom time range
    const useCustomTimeRange = computed({
        get: () => {
            const condition = props.condition;
            return !!(
                condition &&
                condition.time_range &&
                typeof condition.time_range === "object" &&
                condition.time_range !== null
            );
        },
        set: (value) => {
            if (value) {
                // Initialize with global time range if available, or defaults
                const defaultTimeRange = {
                    unit: props.globalTimeRange?.timeRangeUnit || "days",
                    amount: parseInt(props.globalTimeRange?.timeRangeAmount) || 7,
                    exclude_today:
                        props.globalTimeRange?.excludeToday !== undefined ? props.globalTimeRange.excludeToday : true,
                };
                emit("update", { field: "time_range", value: defaultTimeRange });
            } else {
                // Remove custom time range (will use global)
                emit("update", { field: "time_range", value: null });
            }
        },
    });

    const conditionTimeRange = computed({
        get: () => {
            if (props.condition.time_range) {
                const amount = parseInt(props.condition.time_range.amount);
                return {
                    unit: props.condition.time_range.unit || "days",
                    amount: isNaN(amount) ? 7 : amount,
                    exclude_today:
                        props.condition.time_range.exclude_today !== undefined
                            ? props.condition.time_range.exclude_today
                            : true,
                };
            }
            return {
                unit: "days",
                amount: 7,
                exclude_today: true,
            };
        },
        set: (value) => {
            emit("update", { field: "time_range", value });
        },
    });

    const globalTimeRangeLabel = computed(() => {
        if (!props.globalTimeRange || !props.globalTimeRange.timeRangeUnit) {
            return "Not set";
        }
        const unit = props.globalTimeRange.timeRangeUnit;
        const amount = props.globalTimeRange.timeRangeAmount || 1;
        const excludeToday = props.globalTimeRange.excludeToday;

        if (unit === "today") {
            return "Today only";
        }

        const unitLabel = unit === "minutes" ? "min" : unit === "hours" ? "hr" : "day";
        const excludeText = excludeToday ? " (excl. today)" : "";
        return `${amount} ${unitLabel}${amount !== 1 ? "s" : ""}${excludeText}`;
    });

    function toggleCustomTimeRange(value) {
        useCustomTimeRange.value = value;
    }

    function updateTimeRange(field, value) {
        const newTimeRange = {
            ...conditionTimeRange.value,
            [field]: value,
        };
        // Handle special case for "today"
        if (field === "unit" && value === "today") {
            newTimeRange.amount = 1;
            newTimeRange.exclude_today = false;
        }
        // Ensure amount is always an integer
        if (field === "amount") {
            newTimeRange.amount = parseInt(value) || 1;
        }
        emit("update", { field: "time_range", value: newTimeRange });
    }

    return {
        timeRangeUnitOptions,
        useCustomTimeRange,
        conditionTimeRange,
        globalTimeRangeLabel,
        toggleCustomTimeRange,
        updateTimeRange,
    };
}
