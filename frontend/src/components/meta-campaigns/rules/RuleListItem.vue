<template>
    <div class="rule-item" :class="{ 'ungrouped-rule': isUngrouped, 'folder-rule': isInFolder }">
        <i class="pi pi-bars rule-drag-handle"></i>
        <i class="pi pi-bolt rule-icon"></i>
        <div class="rule-content">
            <!-- Column 1: Title and Description -->
            <div class="rule-title-column">
                <div class="rule-name">{{ rule.name }}</div>
                <div v-if="rule.description" class="rule-description">{{ rule.description }}</div>
            </div>

            <!-- Column 2: Status Panel -->
            <div class="rule-meta">
                <div class="rule-meta-line">
                    <Tag
                        :value="rule.enabled ? 'Enabled' : 'Disabled'"
                        :severity="rule.enabled ? 'success' : 'secondary'"
                    />
                    <Tag
                        :value="scheduleDisplay.short"
                        severity="info"
                        :class="['schedule-tag', { 'has-tooltip': scheduleDisplay.isComplex || scheduleDisplay.timezone }]"
                        v-tooltip.top="getScheduleTooltip()"
                    />
                </div>
                <div class="rule-meta-line">
                    <span class="rule-time-inline">
                        <i class="pi pi-history"></i>
                        Last: {{ formatDateWithTimezone(rule.last_run_at, rule.schedule_cron) }}
                    </span>
                </div>
                <div v-if="rule.schedule_cron" class="rule-meta-line">
                    <span class="rule-time">
                        <i class="pi pi-clock"></i>
                        Next: {{ formatDateWithTimezone(rule.next_run_at, rule.schedule_cron) }}
                    </span>
                </div>
            </div>

            <!-- Column 3: Action Buttons -->
            <div class="action-buttons">
                <Button
                    v-if="testingRuleId !== rule.id"
                    icon="pi pi-play"
                    severity="success"
                    text
                    size="small"
                    @click="$emit('test-rule', rule.id)"
                    v-tooltip.top="'Test Rule'"
                />
                <Button
                    v-else
                    severity="danger"
                    text
                    size="small"
                    @click="$emit('cancel-test')"
                    v-tooltip.top="'Cancel Test'"
                >
                    <ProgressSpinner style="width: 14px; height: 14px; margin-right: 6px" strokeWidth="3" />
                    <i class="pi pi-times"></i>
                </Button>
                <Button
                    icon="pi pi-list"
                    severity="info"
                    text
                    size="small"
                    @click="$emit('view-logs', rule.id)"
                    v-tooltip.top="'View Logs'"
                />
                <Button
                    icon="pi pi-pencil"
                    severity="warning"
                    text
                    size="small"
                    @click="$emit('edit-rule', rule.id)"
                    v-tooltip.top="'Edit'"
                />
                <Button
                    icon="pi pi-trash"
                    severity="danger"
                    text
                    size="small"
                    @click="$emit('delete-rule', rule)"
                    v-tooltip.top="'Delete'"
                />
            </div>
        </div>
    </div>
</template>

<script setup>
import Tag from "primevue/tag";
import Button from "primevue/button";
import ProgressSpinner from "primevue/progressspinner";
import { formatSchedule, formatDateWithTimezone, getScheduleDisplay } from "@/utils/cronHelpers";
import { computed } from "vue";

const props = defineProps({
    rule: {
        type: Object,
        required: true,
    },
    testingRuleId: {
        type: [Number, null],
        default: null,
    },
    isUngrouped: {
        type: Boolean,
        default: false,
    },
    isInFolder: {
        type: Boolean,
        default: false,
    },
});

defineEmits(["test-rule", "cancel-test", "view-logs", "edit-rule", "delete-rule"]);

const scheduleDisplay = computed(() => getScheduleDisplay(props.rule.schedule_cron));

function getScheduleTooltip() {
    const display = scheduleDisplay.value;
    
    // If complex schedule, show full schedule
    if (display.isComplex) {
        let tooltip = display.full;
        // Add timezone if not UTC
        if (display.timezone && display.timezone !== "UTC") {
            tooltip += `\nTimezone: ${display.timezone}`;
        }
        return tooltip;
    }
    
    // If has timezone (but not complex), show just timezone
    if (display.timezone && display.timezone !== "UTC") {
        return `Timezone: ${display.timezone}`;
    }
    
    // No tooltip needed
    return null;
}
</script>

<style scoped>
.rule-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: var(--surface-card);
    position: relative;
    border-bottom: 1px solid #e5e7eb !important;
}

.rule-item:last-child {
    border-bottom: none !important;
}

.rule-item.ungrouped-rule {
    border-bottom: 1px solid #e5e7eb !important;
}

.rule-item.folder-rule {
    padding-left: 3rem;
    background: var(--surface-0);
    border-left: 3px solid var(--primary-100);
}

.rule-drag-handle {
    cursor: move;
    color: var(--text-color-secondary);
    align-self: flex-start;
    padding-top: 0.5rem;
}

.rule-icon {
    color: var(--yellow-500);
    font-size: 1.125rem;
    flex-shrink: 0;
    align-self: flex-start;
    padding-top: 0.5rem;
}

.rule-content {
    flex: 1;
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
    min-width: 0;
}

.rule-title-column {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.rule-name {
    font-weight: 600;
    font-size: 0.9375rem;
    color: var(--text-color);
}

.rule-description {
    font-size: 0.875rem;
    color: #6b7280;
}

.rule-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.375rem;
    flex-shrink: 0;
    padding: 0.625rem 0.875rem;
    background: #f8f9fa;
    border-radius: 0.5rem;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    min-width: 280px;
}

.rule-meta-line {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    flex-wrap: wrap;
}

.schedule-tag {
    font-size: 0.75rem;
}

.schedule-tag.has-tooltip {
    cursor: help;
}

.schedule-tag:deep(.p-tag) {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
}

.schedule-tag:deep(.p-tag-value) {
    font-size: 0.75rem;
}

.rule-time-inline,
.rule-time {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.75rem;
    color: #6b7280;
    white-space: nowrap;
}

.rule-time-inline i,
.rule-time i {
    font-size: 0.75rem;
}

.action-buttons {
    display: flex;
    gap: 0.25rem;
    align-items: flex-start;
    flex-shrink: 0;
    padding-top: 0.25rem;
}

@media (max-width: 768px) {
    .rule-content {
        flex-direction: column;
        gap: 1rem;
    }

    .rule-meta {
        width: 100%;
        min-width: unset;
    }

    .action-buttons {
        width: 100%;
        justify-content: flex-start;
        margin-left: 0;
    }
}
</style>
