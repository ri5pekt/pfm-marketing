import { useRuleData } from "./useRuleData";
import { useRuleOperations } from "./useRuleOperations";
import { useRuleLogs } from "./useRuleLogs";
import { useRuleDialogs } from "./useRuleDialogs";
import { useRuleTesting } from "./useRuleTesting";

export function useRules() {
    // Use all composables
    const ruleData = useRuleData();
    const ruleOperations = useRuleOperations();
    const ruleLogs = useRuleLogs();
    const ruleDialogs = useRuleDialogs();
    const ruleTesting = useRuleTesting();

    // Orchestrator function that combines operations and data loading
    async function handleSaveRule(ruleDataParam, accountId) {
        ruleDataParam.ad_account_id = accountId;
        const success = await ruleOperations.saveRule(ruleDataParam);
        if (success) {
            ruleDialogs.closeCreateDialog();
            // Reload rules for the account (not silent so user sees the update)
            if (accountId) {
                await ruleData.loadRules(accountId, false);
            }
            // Reload all rules for counting
            await ruleData.loadAllRules();
        }
        return success;
    }

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
        // State from ruleDialogs
        showCreateDialog: ruleDialogs.showCreateDialog,
        editingRule: ruleDialogs.editingRule,
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
        // Methods from ruleDialogs
        openCreateDialog: ruleDialogs.openCreateDialog,
        editRule: ruleDialogs.editRule,
        closeCreateDialog: ruleDialogs.closeCreateDialog,
        // Methods from ruleTesting
        testRule: ruleTesting.testRule,
        cancelTestRule: ruleTesting.cancelTestRule,
        // Orchestrator
        handleSaveRule,
    };
}
