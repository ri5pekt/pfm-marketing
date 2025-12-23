<template>
    <div v-if="selectedAccount" class="rules-section">
        <div class="section-header">
            <h2>Rules for {{ selectedAccount.name }}</h2>
            <Button label="Create Rule" icon="pi pi-plus" @click="$emit('create-rule')" />
        </div>
        <DataTable
            :value="rules"
            :loading="loading"
            paginator
            :rows="10"
            :rowsPerPageOptions="[10, 20, 50]"
            class="rules-table"
        >
            <Column field="name" header="Name" sortable>
                <template #body="slotProps">
                    <div class="name-column">
                        <div class="name-text">{{ slotProps.data.name }}</div>
                        <div v-if="slotProps.data.description" class="description-text">
                            {{ slotProps.data.description }}
                        </div>
                    </div>
                </template>
            </Column>
            <Column field="schedule_cron" header="Schedule">
                <template #body="slotProps">
                    {{ formatSchedule(slotProps.data.schedule_cron) }}
                </template>
            </Column>
            <Column field="enabled" header="Status">
                <template #body="slotProps">
                    <Tag
                        :value="slotProps.data.enabled ? 'Enabled' : 'Disabled'"
                        :severity="slotProps.data.enabled ? 'success' : 'secondary'"
                    />
                </template>
            </Column>
            <Column field="last_run_at" header="Last Run">
                <template #body="slotProps">
                    <span class="run-time-text">
                        {{ formatDateWithTimezone(slotProps.data.last_run_at, slotProps.data.schedule_cron) }}
                    </span>
                </template>
            </Column>
            <Column field="next_run_at" header="Next Run">
                <template #body="slotProps">
                    <span v-if="slotProps.data.schedule_cron" class="run-time-text">
                        {{ formatDateWithTimezone(slotProps.data.next_run_at, slotProps.data.schedule_cron) }}
                    </span>
                    <span v-else class="text-secondary run-time-text">N/A</span>
                </template>
            </Column>
            <Column header="Actions">
                <template #body="slotProps">
                    <div class="action-buttons">
                        <Button
                            v-if="testingRuleId !== slotProps.data.id"
                            icon="pi pi-play"
                            severity="success"
                            text
                            rounded
                            @click="$emit('test-rule', slotProps.data.id)"
                            v-tooltip.top="'Test Rule'"
                        />
                        <Button
                            v-else
                            severity="danger"
                            text
                            rounded
                            @click="$emit('cancel-test')"
                            v-tooltip.top="'Cancel Test'"
                            class="cancel-test-button"
                        >
                            <ProgressSpinner
                                style="width: 14px; height: 14px; margin-right: 6px"
                                strokeWidth="3"
                                animationDuration="1s"
                            />
                            <i class="pi pi-times"></i>
                        </Button>
                        <Button
                            icon="pi pi-list"
                            severity="info"
                            text
                            rounded
                            @click="$emit('view-logs', slotProps.data.id)"
                            v-tooltip.top="'View Logs'"
                        />
                        <Button
                            icon="pi pi-pencil"
                            severity="warning"
                            text
                            rounded
                            @click="$emit('edit-rule', slotProps.data)"
                            v-tooltip.top="'Edit'"
                        />
                        <Button
                            icon="pi pi-trash"
                            severity="danger"
                            text
                            rounded
                            @click="$emit('delete-rule', slotProps.data)"
                            v-tooltip.top="'Delete'"
                        />
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>
</template>

<script setup>
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import { formatSchedule, formatDateWithTimezone } from '@/utils/cronHelpers'

defineProps({
    selectedAccount: {
        type: Object,
        required: true,
    },
    rules: {
        type: Array,
        default: () => [],
    },
    loading: {
        type: Boolean,
        default: false,
    },
    testingRuleId: {
        type: [Number, null],
        default: null,
    },
})

defineEmits(['create-rule', 'test-rule', 'cancel-test', 'view-logs', 'edit-rule', 'delete-rule'])
</script>

<style scoped>
.rules-section {
    margin-top: 2rem;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.name-column {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.name-text {
    font-weight: 600;
    color: #1f2937;
}

.description-text {
    font-size: 0.875rem;
    color: #6b7280;
}

.run-time-text {
    font-size: 0.875rem;
    color: #374151;
}

.text-secondary {
    color: #6b7280;
}

.action-buttons {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.cancel-test-button {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    min-width: 2.5rem;
}
</style>

