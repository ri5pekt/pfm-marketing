<template>
    <div class="rule-item" :class="{ 'ungrouped-rule': isUngrouped, 'folder-rule': isInFolder }">
        <i class="pi pi-bars rule-drag-handle"></i>
        <i class="pi pi-bolt rule-icon"></i>
        <div class="rule-content">
            <div class="rule-main-line">
                <div class="rule-name">{{ rule.name }}</div>
                <div class="rule-meta">
                    <Tag :value="rule.enabled ? 'Enabled' : 'Disabled'" :severity="rule.enabled ? 'success' : 'secondary'" />
                    <span class="rule-schedule">{{ formatSchedule(rule.schedule_cron) }}</span>
                </div>
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
                    <Button v-else severity="danger" text size="small" @click="$emit('cancel-test')" v-tooltip.top="'Cancel Test'">
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
            <div v-if="rule.description" class="rule-description">{{ rule.description }}</div>
            <div class="rule-times">
                <span class="rule-time">
                    <i class="pi pi-history"></i>
                    Last: {{ formatDateWithTimezone(rule.last_run_at, rule.schedule_cron) }}
                </span>
                <span v-if="rule.schedule_cron" class="rule-time">
                    <i class="pi pi-clock"></i>
                    Next: {{ formatDateWithTimezone(rule.next_run_at, rule.schedule_cron) }}
                </span>
            </div>
        </div>
    </div>
</template>

<script setup>
import Tag from 'primevue/tag';
import Button from 'primevue/button';
import ProgressSpinner from 'primevue/progressspinner';
import { formatSchedule, formatDateWithTimezone } from '@/utils/cronHelpers';

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

defineEmits(['test-rule', 'cancel-test', 'view-logs', 'edit-rule', 'delete-rule']);
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
    flex-direction: column;
    gap: 0;
    min-width: 0;
}

.rule-main-line {
    display: flex;
    align-items: center;
    gap: 1rem;
    width: 100%;
}

.rule-name {
    font-weight: 600;
    font-size: 0.9375rem;
    color: var(--text-color);
    flex-shrink: 0;
}

.rule-description {
    font-size: 0.875rem;
    color: #6b7280;
    margin-top: 0.25rem;
    margin-bottom: 0.75rem;
}

.rule-meta {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
}

.rule-schedule {
    font-size: 0.875rem;
    color: var(--text-color-secondary);
    white-space: nowrap;
}

.rule-times {
    display: flex;
    gap: 1.5rem;
    font-size: 0.8125rem;
    color: #6b7280;
}

.rule-time {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    white-space: nowrap;
}

.rule-time i {
    font-size: 0.875rem;
}

.action-buttons {
    display: flex;
    gap: 0.25rem;
    align-items: center;
    margin-left: auto;
    flex-shrink: 0;
}

@media (max-width: 768px) {
    .rule-main-line {
        flex-direction: column;
        align-items: flex-start;
    }

    .action-buttons {
        width: 100%;
        justify-content: flex-start;
        margin-left: 0;
    }

    .rule-meta {
        flex-wrap: wrap;
    }
}
</style>
