import { weekDays } from "@/utils/cronHelpers";

export function useRuleSchedule(ruleForm, scheduleFormErrors) {
    function onSchedulePeriodChange() {
        // Reset dependent fields when period changes
        ruleForm.value.scheduleDayOfWeek = null;
        ruleForm.value.scheduleDayOfMonth = null;

        // Reset custom daily schedule if switching away from it
        if (ruleForm.value.schedulePeriod !== "daily_custom") {
            ruleForm.value.customDailySchedule = {};
        } else if (ruleForm.value.schedulePeriod === "daily_custom") {
            // Initialize custom daily schedule if empty
            if (!ruleForm.value.customDailySchedule || Object.keys(ruleForm.value.customDailySchedule).length === 0) {
                ruleForm.value.customDailySchedule = {};
            }
        }
    }

    function validateTime(dayValue) {
        const timeKey = dayValue + "_time";
        const time = ruleForm.value.customDailySchedule[timeKey];
        if (time) {
            const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
            if (!timeRegex.test(time)) {
                scheduleFormErrors.value[`day_${dayValue}_time`] = "Time must be in HH:MM format (24-hour)";
            } else {
                delete scheduleFormErrors.value[`day_${dayValue}_time`];
            }
        }
    }

    function validateSchedule() {
        scheduleFormErrors.value = {};
        if (!ruleForm.value.schedulePeriod || ruleForm.value.schedulePeriod === "none") {
            return true;
        }
        if (!ruleForm.value.scheduleFrequency || ruleForm.value.scheduleFrequency < 1) {
            scheduleFormErrors.value.frequency = "Frequency must be at least 1";
        }
        if (ruleForm.value.schedulePeriod === "minute" || ruleForm.value.schedulePeriod === "hourly") {
            // Minute and hourly don't need time, day_of_week, or day_of_month
        } else if (ruleForm.value.schedulePeriod === "daily") {
            if (!ruleForm.value.scheduleTime) {
                scheduleFormErrors.value.time = "Time is required for daily period";
            } else {
                const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
                if (!timeRegex.test(ruleForm.value.scheduleTime)) {
                    scheduleFormErrors.value.time = "Time must be in HH:MM format (24-hour)";
                }
            }
        } else if (ruleForm.value.schedulePeriod === "weekly") {
            if (!ruleForm.value.scheduleTime) {
                scheduleFormErrors.value.time = "Time is required for weekly period";
            } else {
                const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
                if (!timeRegex.test(ruleForm.value.scheduleTime)) {
                    scheduleFormErrors.value.time = "Time must be in HH:MM format (24-hour)";
                }
            }
            if (ruleForm.value.scheduleDayOfWeek === null) {
                scheduleFormErrors.value.dayOfWeek = "Day of week is required for weekly period";
            }
        } else if (ruleForm.value.schedulePeriod === "monthly") {
            if (!ruleForm.value.scheduleTime) {
                scheduleFormErrors.value.time = "Time is required for monthly period";
            } else {
                const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
                if (!timeRegex.test(ruleForm.value.scheduleTime)) {
                    scheduleFormErrors.value.time = "Time must be in HH:MM format (24-hour)";
                }
            }
            if (ruleForm.value.scheduleDayOfMonth === null) {
                scheduleFormErrors.value.dayOfMonth = "Day of month is required for monthly period";
            } else if (ruleForm.value.scheduleDayOfMonth < 1 || ruleForm.value.scheduleDayOfMonth > 31) {
                scheduleFormErrors.value.dayOfMonth = "Day of month must be between 1 and 31";
            }
        } else if (ruleForm.value.schedulePeriod === "daily_custom") {
            const selectedDays = weekDays.filter((day) => ruleForm.value.customDailySchedule[day.value]);
            if (selectedDays.length === 0) {
                scheduleFormErrors.value.customDaily = "At least one day must be selected";
            } else {
                delete scheduleFormErrors.value.customDaily;
                let hasInvalidTime = false;
                selectedDays.forEach((day) => {
                    const timeKey = day.value + "_time";
                    const time = ruleForm.value.customDailySchedule[timeKey];
                    if (!time) {
                        scheduleFormErrors.value[`day_${day.value}_time`] = "Time is required for selected day";
                        hasInvalidTime = true;
                    } else {
                        const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
                        if (!timeRegex.test(time)) {
                            scheduleFormErrors.value[`day_${day.value}_time`] = "Time must be in HH:MM format (24-hour)";
                            hasInvalidTime = true;
                        } else {
                            delete scheduleFormErrors.value[`day_${day.value}_time`];
                        }
                    }
                });
                if (!hasInvalidTime) {
                    delete scheduleFormErrors.value.customDaily;
                }
            }
        }
        return Object.keys(scheduleFormErrors.value).length === 0;
    }

    return {
        onSchedulePeriodChange,
        validateTime,
        validateSchedule,
    };
}

