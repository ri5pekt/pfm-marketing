import { useRuleData } from "./useRuleData";
import { useRuleOperations } from "./useRuleOperations";
import { useRuleLogs } from "./useRuleLogs";
import { useRuleTesting } from "./useRuleTesting";

export function useRules() {
    // Use all composables
    const ruleData = useRuleData();
    const ruleOperations = useRuleOperations();
    const ruleLogs = useRuleLogs();
    const ruleTesting = useRuleTesting();

    // Wrapper for viewLogs that passes rules list
    async function viewLogs(ruleId) {
        await ruleLogs.viewLogs(ruleId, ruleData.rules.value);
    }

    // Wrapper for confirmDeleteLog that passes reload callback
    function confirmDeleteLog(log) {
        ruleLogs.confirmDeleteLog(log, async () => {
            if (ruleLogs.currentRuleForLogs.value) {
                await ruleLogs.viewLogs(ruleLogs.currentRuleForLogs.value.id, ruleData.rules.value);
            }
        });
    }

    return {
        // State from ruleData
        rules: ruleData.rules,
        allRules: ruleData.allRules,
        loading: ruleData.loading,
        // State from ruleOperations
        saving: ruleOperations.saving,
        // State from ruleLogs
        loadingLogs: ruleLogs.loadingLogs,
        showLogsDialog: ruleLogs.showLogsDialog,
        showLogDetailsDialog: ruleLogs.showLogDetailsDialog,
        logs: ruleLogs.logs,
        currentRuleForLogs: ruleLogs.currentRuleForLogs,
        selectedLogDetails: ruleLogs.selectedLogDetails,
        // State from ruleTesting
        testingRuleId: ruleTesting.testingRuleId,
        // Methods from ruleData
        loadAllRules: ruleData.loadAllRules,
        loadRules: ruleData.loadRules,
        getRulesCountForAccount: ruleData.getRulesCountForAccount,
        // Methods from ruleOperations
        saveRule: ruleOperations.saveRule,
        deleteRuleById: ruleOperations.deleteRuleById,
        confirmDelete: ruleOperations.confirmDelete,
        // Methods from ruleLogs
        viewLogs,
        confirmDeleteLog,
        showLogDetails: ruleLogs.showLogDetails,
        downloadLogDetails: ruleLogs.downloadLogDetails,
        closeLogsDialog: ruleLogs.closeLogsDialog,
        closeLogDetailsDialog: ruleLogs.closeLogDetailsDialog,
        // Methods from ruleTesting
        testRule: ruleTesting.testRule,
        cancelTestRule: ruleTesting.cancelTestRule,
    };
}
