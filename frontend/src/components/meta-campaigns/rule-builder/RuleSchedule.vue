<template>
    <div v-if="modelValue.ruleLevel" class="form-section scheduling-section">
        <h3 class="section-title">6. Execution Schedule</h3>

        <div class="field">
            <label>Period</label>
            <Select
                :modelValue="modelValue.schedulePeriod"
                @update:modelValue="update('schedulePeriod', $event)"
                :options="periodOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Select period (optional)"
                class="w-full"
                :class="{ 'p-invalid': errors.period }"
                @change="onSchedulePeriodChange"
            />
            <small v-if="errors.period" class="p-error">{{ errors.period }}</small>
        </div>

        <div
            class="field"
            v-if="
                modelValue.schedulePeriod &&
                modelValue.schedulePeriod !== 'none' &&
                modelValue.schedulePeriod !== 'daily_custom'
            "
        >
            <label>Frequency *</label>
            <InputNumber
                :modelValue="modelValue.scheduleFrequency"
                @update:modelValue="update('scheduleFrequency', $event)"
                :min="1"
                placeholder="Every X"
                class="w-full"
                :class="{ 'p-invalid': errors.frequency }"
            />
            <small v-if="errors.frequency" class="p-error">{{ errors.frequency }}</small>
            <small class="p-text-secondary">
                <span v-if="modelValue.schedulePeriod === 'minute'">Every X minute(s)</span>
                <span v-else-if="modelValue.schedulePeriod === 'hourly'">Every X hour(s)</span>
                <span v-else-if="modelValue.schedulePeriod === 'daily'">Every X day(s)</span>
                <span v-else-if="modelValue.schedulePeriod === 'weekly'">Every X week(s)</span>
                <span v-else-if="modelValue.schedulePeriod === 'monthly'">Every X month(s)</span>
            </small>
        </div>

        <div
            class="field"
            v-if="
                modelValue.schedulePeriod &&
                modelValue.schedulePeriod !== 'none' &&
                (modelValue.schedulePeriod === 'daily' ||
                    modelValue.schedulePeriod === 'weekly' ||
                    modelValue.schedulePeriod === 'monthly')
            "
        >
            <label>Time *</label>
            <InputText
                :modelValue="modelValue.scheduleTime"
                @update:modelValue="update('scheduleTime', $event)"
                placeholder="HH:MM (24-hour format, e.g., 09:00)"
                class="w-full"
                :class="{ 'p-invalid': errors.time }"
            />
            <small v-if="errors.time" class="p-error">{{ errors.time }}</small>
            <small class="p-text-secondary"
                >Time in 24-hour format (e.g., 09:00 for 9 AM, 14:30 for 2:30 PM)</small
            >
        </div>

        <div class="field" v-if="modelValue.schedulePeriod && modelValue.schedulePeriod === 'weekly'">
            <label>Day of Week *</label>
            <Select
                :modelValue="modelValue.scheduleDayOfWeek"
                @update:modelValue="update('scheduleDayOfWeek', $event)"
                :options="dayOfWeekOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Select day"
                class="w-full"
                :class="{ 'p-invalid': errors.dayOfWeek }"
            />
            <small v-if="errors.dayOfWeek" class="p-error">{{ errors.dayOfWeek }}</small>
        </div>

        <div class="field" v-if="modelValue.schedulePeriod && modelValue.schedulePeriod === 'monthly'">
            <label>Day of Month *</label>
            <InputNumber
                :modelValue="modelValue.scheduleDayOfMonth"
                @update:modelValue="update('scheduleDayOfMonth', $event)"
                :min="1"
                :max="31"
                placeholder="1-31"
                class="w-full"
                :class="{ 'p-invalid': errors.dayOfMonth }"
            />
            <small v-if="errors.dayOfMonth" class="p-error">{{ errors.dayOfMonth }}</small>
        </div>

        <!-- Custom Daily Schedule: Day/Time Picker -->
        <div class="field" v-if="modelValue.schedulePeriod === 'daily_custom'">
            <label>Select Days and Times *</label>
            <div class="custom-daily-schedule">
                <div v-for="day in weekDays" :key="day.value" class="custom-daily-row">
                    <div class="day-checkbox">
                        <Checkbox
                            :modelValue="!!modelValue.customDailySchedule[day.value]"
                            @update:modelValue="(val) => onDayToggle(day.value, val)"
                            :inputId="`day-${day.value}`"
                            :binary="true"
                        />
                        <label :for="`day-${day.value}`" class="day-label">{{ day.label }}</label>
                    </div>
                    
                    <div class="schedule-controls" v-if="modelValue.customDailySchedule[day.value]">
                        <div class="time-control">
                            <label class="control-label">Start at:</label>
                            <InputText
                                :modelValue="getDayStartTime(day.value)"
                                @update:modelValue="updateCustomDailyTime(day.value, $event)"
                                :disabled="!modelValue.customDailySchedule[day.value]"
                                placeholder="HH:MM (e.g., 09:00)"
                                class="time-input"
                                :class="{ 'p-invalid': errors[`day_${day.value}_time`] }"
                                @blur="validateTime(day.value)"
                            />
                        </div>
                        
                        <div class="run-mode-control">
                            <Select
                                :modelValue="getDayRunMode(day.value)"
                                @update:modelValue="updateRunMode(day.value, $event)"
                                :options="runModeOptions"
                                optionLabel="label"
                                optionValue="value"
                                placeholder="Run once"
                                class="run-mode-select"
                            />
                        </div>
                        
                        <div class="interval-control" v-if="getDayRunMode(day.value) === 'every'">
                            <Select
                                :modelValue="getDayInterval(day.value)"
                                @update:modelValue="updateInterval(day.value, $event)"
                                :options="intervalOptions"
                                optionLabel="label"
                                optionValue="value"
                                placeholder="Select interval"
                                class="interval-select"
                            />
                            <small class="execution-count" v-if="getDayInterval(day.value)">
                                {{ getExecutionCount(getDayInterval(day.value)) }} times/day
                            </small>
                        </div>
                    </div>
                </div>
            </div>
            <small v-if="errors.customDaily" class="p-error">{{ errors.customDaily }}</small>
            <small class="p-text-secondary"
                >Select days, set start times, and choose execution frequency</small
            >
        </div>

        <div class="field" v-if="modelValue.schedulePeriod && modelValue.schedulePeriod !== 'none'">
            <label>Timezone</label>
            <Select
                :modelValue="modelValue.scheduleTimezone"
                @update:modelValue="update('scheduleTimezone', $event)"
                :options="timezoneOptions"
                placeholder="Select timezone"
                class="w-full"
            />
        </div>
    </div>
</template>

<script setup>
import Select from "primevue/select";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import Checkbox from "primevue/checkbox";
import {
    periodOptions,
    dayOfWeekOptions,
    weekDays,
    timezoneOptions,
} from "@/utils/cronHelpers";

const props = defineProps({
    modelValue: {
        type: Object,
        required: true,
    },
    errors: {
        type: Object,
        default: () => ({}),
    },
});

const emit = defineEmits(["update:modelValue", "schedulePeriodChanged", "validateTime"]);

// Run mode options
const runModeOptions = [
    { label: "Run once", value: "once" },
    { label: "Run every", value: "every" },
];

// Interval options
const intervalOptions = [
    { label: "15 minutes", value: 15 },
    { label: "30 minutes", value: 30 },
    { label: "1 hour", value: 60 },
    { label: "3 hours", value: 180 },
    { label: "6 hours", value: 360 },
    { label: "12 hours", value: 720 },
];

function update(field, value) {
    emit("update:modelValue", {
        ...props.modelValue,
        [field]: value,
    });
}

function onSchedulePeriodChange() {
    // Reset dependent fields when period changes
    const updates = {
        scheduleDayOfWeek: null,
        scheduleDayOfMonth: null,
    };

    // Reset custom daily schedule if switching away from it
    if (props.modelValue.schedulePeriod !== "daily_custom") {
        updates.customDailySchedule = {};
    } else if (props.modelValue.schedulePeriod === "daily_custom") {
        // Initialize custom daily schedule if empty
        if (!props.modelValue.customDailySchedule || Object.keys(props.modelValue.customDailySchedule).length === 0) {
            updates.customDailySchedule = {};
        }
    }

    emit("update:modelValue", {
        ...props.modelValue,
        ...updates,
    });
    emit("schedulePeriodChanged");
}

function onDayToggle(dayValue, checked) {
    const customDailySchedule = { ...props.modelValue.customDailySchedule };
    if (checked) {
        customDailySchedule[dayValue] = true;
        // Set default time if not set
        if (!customDailySchedule[dayValue + "_time"]) {
            customDailySchedule[dayValue + "_time"] = "12:00";
        }
        // Set default run mode if not set
        if (!customDailySchedule[dayValue + "_mode"]) {
            customDailySchedule[dayValue + "_mode"] = "once";
        }
    } else {
        customDailySchedule[dayValue] = false;
        // Clear time and mode when unchecked
        delete customDailySchedule[dayValue + "_time"];
        delete customDailySchedule[dayValue + "_mode"];
        delete customDailySchedule[dayValue + "_interval"];
    }
    update("customDailySchedule", customDailySchedule);
}

function getDayStartTime(dayValue) {
    const timeKey = dayValue + "_time";
    return props.modelValue.customDailySchedule[timeKey] || "12:00";
}

function getDayRunMode(dayValue) {
    const modeKey = dayValue + "_mode";
    return props.modelValue.customDailySchedule[modeKey] || "once";
}

function getDayInterval(dayValue) {
    const intervalKey = dayValue + "_interval";
    return props.modelValue.customDailySchedule[intervalKey] || null;
}

function updateCustomDailyTime(dayValue, time) {
    const customDailySchedule = { ...props.modelValue.customDailySchedule };
    customDailySchedule[dayValue + "_time"] = time;
    update("customDailySchedule", customDailySchedule);
}

function updateRunMode(dayValue, mode) {
    const customDailySchedule = { ...props.modelValue.customDailySchedule };
    customDailySchedule[dayValue + "_mode"] = mode;
    
    // If switching to "once", clear interval
    if (mode === "once") {
        delete customDailySchedule[dayValue + "_interval"];
    } else if (mode === "every" && !customDailySchedule[dayValue + "_interval"]) {
        // Set default interval when switching to "every"
        customDailySchedule[dayValue + "_interval"] = 15;
    }
    
    update("customDailySchedule", customDailySchedule);
}

function updateInterval(dayValue, interval) {
    const customDailySchedule = { ...props.modelValue.customDailySchedule };
    customDailySchedule[dayValue + "_interval"] = interval;
    update("customDailySchedule", customDailySchedule);
}

function getExecutionCount(intervalMinutes) {
    if (!intervalMinutes) return 0;
    
    // Calculate executions for full 24-hour day
    const minutesInDay = 24 * 60;
    return Math.floor(minutesInDay / intervalMinutes);
}

function validateTime(dayValue) {
    emit("validateTime", dayValue);
}
</script>

<style scoped>
.form-section {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.5rem;
    background-color: #f9fafb;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}

.scheduling-section {
    margin-top: 1rem;
}

.section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 1rem 0;
}

.field {
    margin-bottom: 1rem;
}

.field:last-child {
    margin-bottom: 0;
}

.field label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #374151;
}

.p-error {
    color: #ef4444;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

.p-text-secondary {
    color: #6b7280;
    font-size: 0.875rem;
}

.custom-daily-schedule {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 0.5rem;
}

.custom-daily-row {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 0.75rem;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background-color: #fff;
}

.day-checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 120px;
    padding-top: 0.5rem;
}

.day-label {
    font-weight: 500;
    color: #374151;
    cursor: pointer;
    user-select: none;
}

.schedule-controls {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    flex: 1;
    flex-wrap: wrap;
}

.time-control {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.control-label {
    font-size: 0.875rem;
    color: #6b7280;
    white-space: nowrap;
    font-weight: 500;
}

.time-input {
    width: 140px;
}

.time-input:disabled {
    background-color: #f3f4f6;
    color: #9ca3af;
    cursor: not-allowed;
}

.run-mode-control {
    display: flex;
    align-items: center;
}

.run-mode-select {
    width: 140px;
}

.interval-control {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.interval-select {
    width: 140px;
}

.execution-count {
    color: #059669;
    font-size: 0.75rem;
    font-weight: 500;
    white-space: nowrap;
}
</style>

