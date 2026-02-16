<template>
    <div class="logs-view">
        <div class="view-header">
            <div class="header-content">
                <h1>Rule Execution Logs</h1>
                <p class="subtitle">Monitor all rule executions across all ad accounts</p>
            </div>
            <div class="header-actions">
                <Button
                    icon="pi pi-refresh"
                    label="Refresh"
                    :loading="loading"
                    @click="loadLogs"
                    outlined
                />
            </div>
        </div>

        <Card class="logs-card">
            <template #content>
                <DataTable
                    :value="logs"
                    :loading="loading"
                    :rows="rowsPerPage"
                    :paginator="true"
                    :rowsPerPageOptions="[25, 50, 100]"
                    :totalRecords="logs.length"
                    class="logs-table"
                    paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
                    stripedRows
                    responsiveLayout="scroll"
                    sortField="created_at"
                    :sortOrder="-1"
                >
                    <template #empty>
                        <div class="empty-state">
                            <i class="pi pi-inbox" style="font-size: 3rem; color: #94a3b8;"></i>
                            <p>No logs found</p>
                        </div>
                    </template>

                    <Column field="created_at" header="Date" sortable style="width: 180px;">
                        <template #body="{ data }">
                            <span class="log-date">{{ formatDate(data.created_at) }}</span>
                        </template>
                    </Column>

                    <Column field="status" header="Status" sortable style="width: 120px;">
                        <template #body="{ data }">
                            <Tag
                                :value="data.status.toUpperCase()"
                                :severity="getStatusSeverity(data.status)"
                            />
                        </template>
                    </Column>

                    <Column field="ad_account_name" header="Ad Account" sortable style="width: 200px;">
                        <template #body="{ data }">
                            <span class="account-name">{{ data.ad_account_name }}</span>
                        </template>
                    </Column>

                    <Column field="rule_name" header="Rule" sortable style="width: 250px;">
                        <template #body="{ data }">
                            <span class="rule-name">{{ data.rule_name }}</span>
                        </template>
                    </Column>

                    <Column field="message" header="Message" style="min-width: 300px;">
                        <template #body="{ data }">
                            <span class="log-message">{{ data.message }}</span>
                        </template>
                    </Column>

                    <Column header="Actions" style="width: 150px;">
                        <template #body="{ data }">
                            <div class="log-actions">
                                <Button
                                    icon="pi pi-eye"
                                    severity="secondary"
                                    text
                                    rounded
                                    @click="viewDetails(data)"
                                    v-tooltip.top="'View Details'"
                                />
                                <Button
                                    v-if="data.details"
                                    icon="pi pi-download"
                                    severity="secondary"
                                    text
                                    rounded
                                    @click="downloadLog(data)"
                                    v-tooltip.top="'Download Detailed Log'"
                                />
                            </div>
                        </template>
                    </Column>
                </DataTable>
            </template>
        </Card>

        <!-- Log Details Dialog - Using same component as rule-specific logs -->
        <LogDetailsDialog
            v-model="showDetailsDialog"
            :log-details="selectedLog"
        />
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useToast } from "primevue/usetoast";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Button from "primevue/button";
import Card from "primevue/card";
import Tag from "primevue/tag";
import LogDetailsDialog from "@/components/meta-campaigns/dialogs/LogDetailsDialog.vue";
import { getAllLogs } from "@/api/metaCampaignsApi";

const toast = useToast();
const logs = ref([]);
const loading = ref(false);
const rowsPerPage = ref(25);
const showDetailsDialog = ref(false);
const selectedLog = ref(null);

onMounted(() => {
    loadLogs();
});

async function loadLogs() {
    loading.value = true;
    try {
        logs.value = await getAllLogs({ limit: 500 });
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: error.message || "Failed to load logs",
            life: 5000,
        });
    } finally {
        loading.value = false;
    }
}

function viewDetails(log) {
    selectedLog.value = log;
    showDetailsDialog.value = true;
}

function downloadLog(log) {
    const logData = {
        log_id: log.id,
        rule_id: log.rule_id,
        rule_name: log.rule_name,
        ad_account_id: log.ad_account_id,
        ad_account_name: log.ad_account_name,
        status: log.status,
        message: log.message,
        created_at: log.created_at,
        details: log.details
    };

    const blob = new Blob([JSON.stringify(logData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    
    // Create filename with rule name and timestamp
    const timestamp = new Date(log.created_at).toISOString().replace(/[:.]/g, "-").slice(0, -5);
    const ruleName = log.rule_name.replace(/[^a-z0-9]/gi, "_").toLowerCase();
    link.download = `log_${ruleName}_${timestamp}.json`;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    toast.add({
        severity: "success",
        summary: "Downloaded",
        detail: "Log file downloaded successfully",
        life: 3000,
    });
}

function formatDate(dateString) {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleString();
}

function getStatusSeverity(status) {
    switch (status) {
        case "success":
            return "success";
        case "error":
            return "danger";
        case "skipped":
            return "warn";
        default:
            return "info";
    }
}
</script>

<style scoped>
.logs-view {
    padding: 2rem;
    max-width: 1600px;
    margin: 0 auto;
}

.view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e5e7eb;
}

.header-content h1 {
    font-size: 2rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
}

.subtitle {
    color: #6b7280;
    margin: 0;
}

.header-actions {
    display: flex;
    gap: 0.75rem;
}

.logs-card {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.logs-table {
    font-size: 0.875rem;
}

.log-date {
    color: #4b5563;
    font-family: "Courier New", monospace;
}

.account-name {
    font-weight: 500;
    color: #1f2937;
}

.rule-name {
    color: #2563eb;
    font-weight: 500;
}

.log-message {
    color: #4b5563;
}

.empty-state {
    text-align: center;
    padding: 3rem 0;
}

.empty-state p {
    color: #6b7280;
    margin-top: 1rem;
    font-size: 1rem;
}

.log-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}
</style>
