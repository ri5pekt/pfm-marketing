import { useRouter } from "vue-router";

/**
 * Composable for rule actions
 * Handles rule operations like test, view logs, edit, delete, and navigation
 */
export function useRuleActions(props, emit) {
    const router = useRouter();

    function handleTestRule(ruleId) {
        emit("test-rule", ruleId);
    }

    function handleCancelTest() {
        emit("cancel-test");
    }

    function handleViewLogs(ruleId) {
        emit("view-logs", ruleId);
    }

    function handleDeleteRule(rule) {
        emit("delete-rule", rule);
    }

    function handleToggleRule(rule) {
        emit("toggle-rule", rule);
    }

    function navigateToCreateRule() {
        router.push({
            name: "rule-create",
            query: { accountId: props.selectedAccount.id },
        });
    }

    function navigateToEditRule(ruleId) {
        router.push({
            name: "rule-edit",
            params: { id: ruleId },
            // No accountId needed - rule already has ad_account_id
        });
    }

    return {
        handleTestRule,
        handleCancelTest,
        handleViewLogs,
        handleDeleteRule,
        handleToggleRule,
        navigateToCreateRule,
        navigateToEditRule,
    };
}
