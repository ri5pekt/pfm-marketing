import { ref } from "vue";
import { useToast } from "primevue/usetoast";
import { testRule as testRuleApi } from "@/api/metaCampaignsApi";

export function useRuleTesting() {
    const toast = useToast();

    const testingRuleId = ref(null);
    const testRuleAbortController = ref(null);

    async function testRule(ruleId, onComplete) {
        testingRuleId.value = ruleId;
        testRuleAbortController.value = new AbortController();
        try {
            const result = await testRuleApi(ruleId, testRuleAbortController.value.signal);
            toast.add({
                severity: result.decision === "proceed" ? "success" : "info",
                summary: "Rule Test Complete",
                detail: result.message || "Rule test completed",
                life: 5000,
            });
            if (onComplete) {
                onComplete();
            }
            return result;
        } catch (error) {
            // Don't show error toast if it was cancelled
            if (error.name === "AbortError" || error.message?.includes("aborted")) {
                toast.add({
                    severity: "info",
                    summary: "Test Cancelled",
                    detail: "Rule test was cancelled",
                    life: 3000,
                });
            } else {
                toast.add({
                    severity: "error",
                    summary: "Error",
                    detail: error.message || "Failed to test rule",
                    life: 5000,
                });
            }
            throw error;
        } finally {
            testingRuleId.value = null;
            testRuleAbortController.value = null;
        }
    }

    function cancelTestRule() {
        if (testRuleAbortController.value) {
            testRuleAbortController.value.abort();
            testingRuleId.value = null;
            testRuleAbortController.value = null;
        }
    }

    return {
        testingRuleId,
        testRuleAbortController,
        testRule,
        cancelTestRule,
    };
}

