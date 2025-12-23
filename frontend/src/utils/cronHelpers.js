/**
 * Cron expression building and parsing utilities
 */

export const periodOptions = [
    { label: "None", value: "none" },
    { label: "Minute", value: "minute" },
    { label: "Hourly", value: "hourly" },
    { label: "Daily", value: "daily" },
    { label: "Daily at Custom Times", value: "daily_custom" },
    { label: "Weekly", value: "weekly" },
    { label: "Monthly", value: "monthly" },
];

export const dayOfWeekOptions = [
    { label: "Monday", value: 1 },
    { label: "Tuesday", value: 2 },
    { label: "Wednesday", value: 3 },
    { label: "Thursday", value: 4 },
    { label: "Friday", value: 5 },
    { label: "Saturday", value: 6 },
    { label: "Sunday", value: 0 },
];

export const weekDays = [
    { label: "Sunday", value: 0 },
    { label: "Monday", value: 1 },
    { label: "Tuesday", value: 2 },
    { label: "Wednesday", value: 3 },
    { label: "Thursday", value: 4 },
    { label: "Friday", value: 5 },
    { label: "Saturday", value: 6 },
];

export const timezoneOptions = [
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Paris",
    "Asia/Jerusalem",
    "Asia/Tokyo",
    "Australia/Sydney",
];

/**
 * Build a cron expression from form data
 */
export function buildCronExpression(ruleForm) {
    const {
        schedulePeriod,
        scheduleFrequency,
        scheduleTime,
        scheduleDayOfWeek,
        scheduleDayOfMonth,
        customDailySchedule,
        scheduleTimezone,
    } = ruleForm;

    if (!schedulePeriod || schedulePeriod === "none") {
        return null;
    }

    // Handle custom daily schedule - store as JSON string
    if (schedulePeriod === "daily_custom") {
        const schedule = {};
        weekDays.forEach((day) => {
            if (customDailySchedule[day.value]) {
                const time = customDailySchedule[day.value + "_time"];
                if (time) {
                    schedule[day.value] = time;
                }
            }
        });
        // Store as JSON string with prefix to identify it, including timezone
        return JSON.stringify({
            type: "custom_daily",
            schedule: schedule,
            timezone: scheduleTimezone || "UTC",
        });
    }

    let cron = "";

    if (schedulePeriod === "minute") {
        // Every X minutes: */X * * * *
        cron = `*/${scheduleFrequency} * * * *`;
    } else if (schedulePeriod === "hourly") {
        // Every X hours: 0 */X * * *
        cron = `0 */${scheduleFrequency} * * *`;
    } else if (schedulePeriod === "daily") {
        // Daily at specific time: minute hour * * *
        const [hour, minute] = scheduleTime ? scheduleTime.split(":") : ["0", "0"];
        if (scheduleFrequency === 1) {
            cron = `${minute || 0} ${hour || 0} * * *`;
        } else {
            // For frequency > 1, we approximate with day of month pattern
            cron = `${minute || 0} ${hour || 0} */${scheduleFrequency} * *`;
        }
    } else if (schedulePeriod === "weekly") {
        // Weekly on specific day at specific time: minute hour * * dayOfWeek
        const [hour, minute] = scheduleTime ? scheduleTime.split(":") : ["0", "0"];
        const cronDayOfWeek = scheduleDayOfWeek !== null && scheduleDayOfWeek !== undefined ? scheduleDayOfWeek : "*";
        cron = `${minute || 0} ${hour || 0} * * ${cronDayOfWeek}`;
    } else if (schedulePeriod === "monthly") {
        // Monthly on specific day at specific time: minute hour dayOfMonth * *
        const [hour, minute] = scheduleTime ? scheduleTime.split(":") : ["0", "0"];
        const day = scheduleDayOfMonth || 1;
        if (scheduleFrequency === 1) {
            cron = `${minute || 0} ${hour || 0} ${day} * *`;
        } else {
            cron = `${minute || 0} ${hour || 0} ${day} */${scheduleFrequency} *`;
        }
    }

    // Wrap all schedule types in JSON to include timezone
    const timezone = scheduleTimezone || "UTC";
    return JSON.stringify({
        type: schedulePeriod,
        cron: cron,
        timezone: timezone,
    });
}

/**
 * Parse a cron expression into form data
 */
export function parseCronExpression(cron) {
    if (!cron) {
        return {
            period: "none",
            frequency: 1,
            time: null,
            dayOfWeek: null,
            dayOfMonth: null,
            timezone: "UTC",
            customDailySchedule: {},
        };
    }

    // Check if it's a JSON-wrapped schedule
    try {
        const parsed = JSON.parse(cron);

        // Handle custom daily schedule
        if (parsed.type === "custom_daily" && parsed.schedule) {
            const customSchedule = {};
            Object.keys(parsed.schedule).forEach((dayValue) => {
                customSchedule[dayValue] = true;
                customSchedule[dayValue + "_time"] = parsed.schedule[dayValue];
            });
            return {
                period: "daily_custom",
                frequency: 1,
                time: null,
                dayOfWeek: null,
                dayOfMonth: null,
                timezone: parsed.timezone || "UTC",
                customDailySchedule: customSchedule,
            };
        }

        // Handle other schedule types wrapped in JSON
        if (parsed.type && parsed.cron) {
            const cronParsed = parseCronStringOnly(parsed.cron);
            cronParsed.timezone = parsed.timezone || "UTC";
            return cronParsed;
        }
    } catch (e) {
        // Not JSON, continue with legacy cron parsing
    }

    // Legacy plain cron string
    return parseCronStringOnly(cron);
}

/**
 * Parse just the cron string part (not JSON-wrapped)
 */
export function parseCronStringOnly(cron) {
    const parts = cron.split(/\s+/);
    if (parts.length !== 5) {
        return {
            period: null,
            frequency: 1,
            time: null,
            dayOfWeek: null,
            dayOfMonth: null,
            timezone: "UTC",
            customDailySchedule: {},
        };
    }

    const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;
    let period = null;
    let frequency = 1;
    let time = null;
    let parsedDayOfWeek = null;
    let parsedDayOfMonth = null;

    // Detect pattern
    if (minute.startsWith("*/")) {
        period = "minute";
        frequency = parseInt(minute.substring(2)) || 1;
    } else if (hour.startsWith("*/") && !minute.startsWith("*/") && minute !== "*") {
        period = "hourly";
        frequency = parseInt(hour.substring(2)) || 1;
    } else if (dayOfMonth.startsWith("*/") && month === "*" && dayOfWeek === "*") {
        period = "daily";
        frequency = parseInt(dayOfMonth.substring(2)) || 1;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    } else if (month.startsWith("*/") && dayOfMonth !== "*" && dayOfWeek !== "*") {
        period = "monthly";
        frequency = parseInt(month.substring(2)) || 1;
        parsedDayOfMonth = parseInt(dayOfMonth) || null;
        parsedDayOfWeek = parseInt(dayOfWeek) !== null ? parseInt(dayOfWeek) : null;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    } else if (month.startsWith("*/") && dayOfMonth !== "*" && dayOfWeek === "*") {
        period = "monthly";
        frequency = parseInt(month.substring(2)) || 1;
        parsedDayOfMonth = parseInt(dayOfMonth) || null;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    } else if (dayOfWeek !== "*" && month === "*" && dayOfMonth === "*") {
        period = "weekly";
        frequency = 1;
        parsedDayOfWeek = parseInt(dayOfWeek) !== null ? parseInt(dayOfWeek) : null;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    } else if (dayOfMonth !== "*" && month === "*" && dayOfWeek === "*") {
        period = "monthly";
        frequency = 1;
        parsedDayOfMonth = parseInt(dayOfMonth) || null;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    } else if (dayOfMonth === "*" && month === "*" && dayOfWeek === "*") {
        period = "daily";
        frequency = 1;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    }

    return {
        period,
        frequency,
        time,
        dayOfWeek: parsedDayOfWeek,
        dayOfMonth: parsedDayOfMonth,
        timezone: "UTC", // Legacy cron expressions default to UTC
        customDailySchedule: {},
    };
}

/**
 * Get timezone from schedule cron expression
 */
export function getTimezoneFromSchedule(scheduleCron) {
    if (!scheduleCron) return null;
    try {
        const parsed = JSON.parse(scheduleCron);
        if (parsed.timezone) {
            return parsed.timezone;
        }
    } catch (e) {
        // Not JSON, return null (legacy format defaults to UTC)
    }
    return null;
}

/**
 * Format date with timezone from schedule
 */
export function formatDateWithTimezone(date, scheduleCron) {
    if (!date) return "Never";
    const timezone = getTimezoneFromSchedule(scheduleCron);
    const dateObj = new Date(date);

    if (timezone) {
        const options = {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            timeZone: timezone,
            hour12: false,
        };
        const formatted = dateObj.toLocaleString("en-US", options);
        const tzAbbr =
            new Intl.DateTimeFormat("en-US", {
                timeZone: timezone,
                timeZoneName: "short",
            })
                .formatToParts(dateObj)
                .find((part) => part.type === "timeZoneName")?.value || timezone;
        return `${formatted} (${tzAbbr})`;
    } else {
        return dateObj.toLocaleString();
    }
}

/**
 * Format schedule cron expression to human-readable string
 */
export function formatSchedule(scheduleCron) {
    if (!scheduleCron) return "Manual only";

    let cronExpr = scheduleCron;
    let timezone = "UTC";

    // Check if it's a JSON-wrapped schedule
    try {
        const parsed = JSON.parse(scheduleCron);

        // Handle custom daily schedule
        if (parsed.type === "custom_daily" && parsed.schedule) {
            const schedule = parsed.schedule;
            timezone = parsed.timezone || "UTC";

            const scheduleParts = [];
            const sortedDays = Object.keys(schedule)
                .map(Number)
                .sort((a, b) => a - b);

            for (const dayNum of sortedDays) {
                const dayName = weekDays.find((d) => d.value === dayNum)?.label || `Day ${dayNum}`;
                const time = schedule[dayNum.toString()];
                scheduleParts.push(`${dayName} at ${time}`);
            }

            if (scheduleParts.length === 0) {
                return "No schedule set";
            }

            const scheduleText = scheduleParts.join(", ");
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }

        // Handle other JSON-wrapped schedule types
        if (parsed.type && parsed.cron) {
            cronExpr = parsed.cron;
            timezone = parsed.timezone || "UTC";
        }
    } catch (e) {
        // Not JSON, use as-is (legacy format)
    }

    // Parse as regular cron expression
    const parts = cronExpr.trim().split(/\s+/);
    if (parts.length === 5) {
        const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;

        // Every X minutes
        if (minute.startsWith("*/")) {
            const freq = minute.substring(2);
            const scheduleText = `Every ${freq} minute${freq !== "1" ? "s" : ""}`;
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }

        // Every X hours
        if (hour.startsWith("*/") && minute !== "*" && !minute.startsWith("*/")) {
            const freq = hour.substring(2);
            const scheduleText = `Every ${freq} hour${freq !== "1" ? "s" : ""} at :${minute.padStart(2, "0")}`;
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }

        // Daily at specific time
        if (dayOfMonth === "*" && month === "*" && dayOfWeek === "*" && hour !== "*" && minute !== "*") {
            const time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
            if (dayOfMonth.startsWith("*/")) {
                const freq = dayOfMonth.substring(2);
                const scheduleText = `Every ${freq} day${freq !== "1" ? "s" : ""} at ${time}`;
                return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
            }
            const scheduleText = `Daily at ${time}`;
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }

        // Weekly on specific day
        if (dayOfWeek !== "*" && month === "*" && dayOfMonth === "*" && hour !== "*" && minute !== "*") {
            const dayName = weekDays.find((d) => d.value === parseInt(dayOfWeek))?.label || `Day ${dayOfWeek}`;
            const time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
            const scheduleText = `Every ${dayName} at ${time}`;
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }

        // Monthly on specific day
        if (dayOfMonth !== "*" && month === "*" && dayOfWeek === "*" && hour !== "*" && minute !== "*") {
            const time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
            let scheduleText;
            if (month.startsWith("*/")) {
                const freq = month.substring(2);
                scheduleText = `Every ${freq} month${freq !== "1" ? "s" : ""} on day ${dayOfMonth} at ${time}`;
            } else {
                scheduleText = `Monthly on day ${dayOfMonth} at ${time}`;
            }
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }
    }

    // Fallback: return the cron expression as-is
    return scheduleCron;
}

