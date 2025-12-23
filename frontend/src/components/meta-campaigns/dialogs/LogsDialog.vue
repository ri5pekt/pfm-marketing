<template>
    <Dialog
        :visible="modelValue"
        header="Rule Execution Logs"
        :modal="true"
        :style="{ maxWidth: '900px', width: '90vw', maxHeight: '90vh' }"
        class="logs-dialog"
        @update:visible="$emit('update:modelValue', $event)"
    >
        <div v-if="logs.length === 0 && !loading" class="empty-message">
            <p>No logs available for this rule.</p>
        </div>
        <div v-else class="logs-table-wrapper">
            <DataTable :value="logs" :loading="loading" paginator :rows="10" :rowsPerPageOptions="[10, 20, 50]">
                <Column field="status" header="Status" style="width: 100px">
                    <template #body="slotProps">
                        <Tag :value="slotProps.data.status" :severity="getStatusSeverity(slotProps.data.status)" />
                    </template>
                </Column>
                <Column
                    field="message"
                    header="Message"
                    style="word-wrap: break-word; overflow-wrap: break-word; white-space: normal; max-width: 300px"
                >
                    <template #body="slotProps">
                        <span class="message-text">{{ slotProps.data.message }}</span>
                    </template>
                </Column>
                <Column field="created_at" header="Time" style="width: 180px">
                    <template #body="slotProps">
                        {{ formatDate(slotProps.data.created_at) }}
                    </template>
                </Column>
                <Column header="Actions" style="width: 180px">
                    <template #body="slotProps">
                        <div class="log-actions">
                            <Button
                                v-if="slotProps.data.details"
                                icon="pi pi-eye"
                                severity="secondary"
                                text
                                rounded
                                size="small"
                                @click="$emit('show-details', slotProps.data)"
                                v-tooltip.top="'View Details'"
                            />
                            <Button
                                v-if="slotProps.data.details"
                                icon="pi pi-download"
                                severity="secondary"
                                text
                                rounded
                                size="small"
                                @click="$emit('download', slotProps.data)"
                                v-tooltip.top="'Download Detailed Log'"
                            />
                            <Button
                                icon="pi pi-trash"
                                severity="danger"
                                text
                                rounded
                                size="small"
                                @click="$emit('delete', slotProps.data)"
                                v-tooltip.top="'Delete Log Entry'"
                            />
                        </div>
                    </template>
                </Column>
            </DataTable>
        </div>
    </Dialog>
</template>

<script setup>
import Dialog from 'primevue/dialog'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'

defineProps({
    modelValue: {
        type: Boolean,
        default: false,
    },
    logs: {
        type: Array,
        default: () => [],
    },
    loading: {
        type: Boolean,
        default: false,
    },
})

defineEmits(['update:modelValue', 'show-details', 'download', 'delete'])

function getStatusSeverity(status) {
    if (!status) return 'secondary'
    const upperStatus = status.toUpperCase()
    if (upperStatus === 'SUCCESS') return 'success'
    if (upperStatus === 'ERROR' || upperStatus === 'FAILED') return 'danger'
    if (upperStatus === 'WARNING') return 'warning'
    return 'secondary'
}

function formatDate(date) {
    if (!date) return ''
    const d = new Date(date)
    return d.toLocaleString()
}
</script>

<style scoped>
.empty-message {
    padding: 2rem;
    text-align: center;
    color: #6b7280;
}

.logs-table-wrapper {
    max-width: 100%;
    overflow-x: hidden;
    width: 100%;
    box-sizing: border-box;
}

.log-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.message-text {
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-all;
    white-space: normal;
    max-width: 100%;
    display: inline-block;
}
</style>

