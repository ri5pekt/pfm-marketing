import { ref } from "vue";
import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import { createRule, updateRule, deleteRule } from "@/api/metaCampaignsApi";

export function useRuleOperations() {
    const toast = useToast();
    const confirm = useConfirm();

    const saving = ref(false);

    async function saveRule(ruleData) {
        saving.value = true;
        try {
            if (ruleData.id) {
                await updateRule(ruleData.id, ruleData);
                toast.add({
                    severity: "success",
                    summary: "Success",
                    detail: "Rule updated successfully",
                    life: 3000,
                });
            } else {
                await createRule(ruleData);
                toast.add({
                    severity: "success",
                    summary: "Success",
                    detail: "Rule created successfully",
                    life: 3000,
                });
            }
            return true;
        } catch (error) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to save rule",
                life: 5000,
            });
            return false;
        } finally {
            saving.value = false;
        }
    }

    async function deleteRuleById(ruleId) {
        try {
            await deleteRule(ruleId);
            toast.add({
                severity: "success",
                summary: "Success",
                detail: "Rule deleted successfully",
                life: 3000,
            });
            return true;
        } catch (error) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to delete rule",
                life: 5000,
            });
            return false;
        }
    }

    function confirmDelete(rule, onAccept) {
        confirm.require({
            message: `Are you sure you want to delete the rule "${rule.name}"? This action cannot be undone.`,
            header: "Confirm Delete",
            icon: "pi pi-exclamation-triangle",
            accept: async () => {
                const success = await deleteRuleById(rule.id);
                if (success && onAccept) {
                    onAccept();
                }
            },
        });
    }

    return {
        saving,
        saveRule,
        deleteRuleById,
        confirmDelete,
    };
}

