import { ref } from "vue";
import { useToast } from "primevue/usetoast";
import { getRules } from "@/api/metaCampaignsApi";

export function useRuleData() {
    const toast = useToast();

    const rules = ref([]);
    const allRules = ref([]); // Store all rules for counting across accounts
    const loading = ref(false);

    async function loadAllRules() {
        try {
            allRules.value = await getRules(); // Load all rules without account filter
        } catch (error) {
            // Silently fail - don't show error for background refresh
        }
    }

    async function loadRules(accountId, silent = false) {
        if (!accountId) {
            rules.value = [];
            return;
        }

        if (!silent) {
            loading.value = true;
        }
        try {
            const loadedRules = await getRules(accountId);
            // API returns array directly
            rules.value = Array.isArray(loadedRules) ? loadedRules : [];
            // Also refresh all rules for counting
            await loadAllRules();
        } catch (error) {
            console.error("Failed to load rules:", error);
            rules.value = [];
            // Only show error toast if not silent (manual refresh)
            if (!silent) {
                toast.add({
                    severity: "error",
                    summary: "Error",
                    detail: error.message || "Failed to load rules",
                    life: 5000,
                });
            }
        } finally {
            if (!silent) {
                loading.value = false;
            }
        }
    }

    function getRulesCountForAccount(accountId) {
        if (!accountId || !allRules.value) return 0;
        return allRules.value.filter((rule) => rule.ad_account_id === accountId).length;
    }

    return {
        rules,
        allRules,
        loading,
        loadAllRules,
        loadRules,
        getRulesCountForAccount,
    };
}

