import { ref } from "vue";

export function useRuleDialogs() {
    const showCreateDialog = ref(false);
    const editingRule = ref(null);

    function openCreateDialog() {
        editingRule.value = null;
        showCreateDialog.value = true;
    }

    function editRule(rule) {
        editingRule.value = rule;
        showCreateDialog.value = true;
    }

    function closeCreateDialog() {
        showCreateDialog.value = false;
        editingRule.value = null;
    }

    return {
        showCreateDialog,
        editingRule,
        openCreateDialog,
        editRule,
        closeCreateDialog,
    };
}

