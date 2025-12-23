import { ref } from "vue";
import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import { getRuleLogs, deleteRuleLog } from "@/api/metaCampaignsApi";

export function useRuleLogs() {
    const toast = useToast();
    const confirm = useConfirm();

    const logs = ref([]);
    const loadingLogs = ref(false);
    const showLogsDialog = ref(false);
    const showLogDetailsDialog = ref(false);
    const currentRuleForLogs = ref(null);
    const selectedLogDetails = ref(null);

    async function viewLogs(ruleId, rulesList) {
        showLogsDialog.value = true;
        loadingLogs.value = true;
        try {
            // Store the rule ID for reference in downloads
            currentRuleForLogs.value = rulesList.find((r) => r.id === ruleId) || null;
            logs.value = await getRuleLogs(ruleId);
        } catch (error) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: "Failed to load logs",
                life: 5000,
            });
        } finally {
            loadingLogs.value = false;
        }
    }

    function confirmDeleteLog(log, onAccept) {
        confirm.require({
            message: `Are you sure you want to delete this log entry? This will remove the log from the database. Note: Any downloaded files on your computer will not be deleted.`,
            header: "Confirm Delete",
            icon: "pi pi-exclamation-triangle",
            accept: async () => {
                try {
                    if (!currentRuleForLogs.value) {
                        toast.add({
                            severity: "error",
                            summary: "Error",
                            detail: "Cannot delete: Rule context missing",
                            life: 3000,
                        });
                        return;
                    }
                    await deleteRuleLog(currentRuleForLogs.value.id, log.id);
                    toast.add({
                        severity: "success",
                        summary: "Success",
                        detail: "Log entry deleted successfully",
                        life: 3000,
                    });
                    // Reload logs
                    if (onAccept) {
                        onAccept();
                    }
                } catch (error) {
                    toast.add({
                        severity: "error",
                        summary: "Error",
                        detail: error.message || "Failed to delete log",
                        life: 5000,
                    });
                }
            },
        });
    }

    function showLogDetails(log) {
        selectedLogDetails.value = log;
        showLogDetailsDialog.value = true;
    }

    function downloadLogDetails(log) {
        if (!log.details) {
            toast.add({
                severity: "warn",
                summary: "No Details",
                detail: "This log entry does not have detailed information",
                life: 3000,
            });
            return;
        }

        const dataStr = JSON.stringify(log.details, null, 2);
        const dataBlob = new Blob([dataStr], { type: "application/json" });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement("a");
        link.href = url;
        const ruleName = currentRuleForLogs.value?.name || "rule";
        const timestamp = log.created_at ? new Date(log.created_at).toISOString().replace(/[:.]/g, "-") : "unknown";
        link.download = `${ruleName}-log-${log.id}-${timestamp}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        toast.add({
            severity: "success",
            summary: "Downloaded",
            detail: "Log details downloaded successfully",
            life: 3000,
        });
    }

    function closeLogsDialog() {
        showLogsDialog.value = false;
        logs.value = [];
        currentRuleForLogs.value = null;
    }

    function closeLogDetailsDialog() {
        showLogDetailsDialog.value = false;
        selectedLogDetails.value = null;
    }

    return {
        logs,
        loadingLogs,
        showLogsDialog,
        showLogDetailsDialog,
        currentRuleForLogs,
        selectedLogDetails,
        viewLogs,
        confirmDeleteLog,
        showLogDetails,
        downloadLogDetails,
        closeLogsDialog,
        closeLogDetailsDialog,
    };
}

