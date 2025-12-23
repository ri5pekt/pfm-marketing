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
                    <InputText
                        :modelValue="modelValue.customDailySchedule[day.value + '_time']"
                        @update:modelValue="updateCustomDailyTime(day.value, $event)"
                        :disabled="!modelValue.customDailySchedule[day.value]"
                        placeholder="HH:MM (e.g., 09:00)"
                        class="time-input"
                        :class="{ 'p-invalid': errors[`day_${day.value}_time`] }"
                        @blur="validateTime(day.value)"
                    />
                </div>
            </div>
            <small v-if="errors.customDaily" class="p-error">{{ errors.customDaily }}</small>
            <small class="p-text-secondary"
                >Select days and set execution times in 24-hour format</small
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
    if (!customDailySchedule) {
        customDailySchedule = {};
    }
    if (checked) {
        customDailySchedule[dayValue] = true;
        // Set default time if not set
        if (!customDailySchedule[dayValue + "_time"]) {
            customDailySchedule[dayValue + "_time"] = "12:00";
        }
    } else {
        customDailySchedule[dayValue] = false;
        // Clear time when unchecked
        delete customDailySchedule[dayValue + "_time"];
    }
    update("customDailySchedule", customDailySchedule);
}

function updateCustomDailyTime(dayValue, time) {
    const customDailySchedule = { ...props.modelValue.customDailySchedule };
    customDailySchedule[dayValue + "_time"] = time;
    update("customDailySchedule", customDailySchedule);
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
    align-items: center;
    gap: 1rem;
    padding: 0.5rem;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background-color: #fff;
}

.day-checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 120px;
}

.day-label {
    font-weight: 500;
    color: #374151;
    cursor: pointer;
    user-select: none;
}

.time-input {
    flex: 1;
    max-width: 150px;
}

.time-input:disabled {
    background-color: #f3f4f6;
    color: #9ca3af;
    cursor: not-allowed;
}
</style>

