<template>
    <div class="meta-campaigns">
        <div class="page-header">
            <h1>Ad Accounts</h1>
            <div class="header-actions">
                <Button
                    label="Create Ad Account"
                    icon="pi pi-plus"
                    severity="secondary"
                    outlined
                    @click="openCreateAdAccountDialog"
                />
            </div>
        </div>

        <!-- Ad Accounts Section -->
        <AdAccountsSection
            :adAccounts="adAccounts"
            :loading="loadingAccounts"
            :selectedAccount="selectedAccount"
            :getRulesCount="getRulesCountForAccount"
            @account-selected="onAccountSelect"
            @edit-account="editAdAccount"
            @delete-account="confirmDeleteAccount"
        />

        <!-- Campaigns Section Toggle (shown when account is selected) -->
        <div v-if="selectedAccount" class="campaigns-toggle-section">
            <Button
                :label="showCampaigns ? 'Hide Campaigns' : `Show Campaigns for ${selectedAccount.name}`"
                :icon="showCampaigns ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
                severity="secondary"
                outlined
                @click="showCampaigns = !showCampaigns"
                class="campaigns-toggle-button"
            />
        </div>

        <!-- Campaigns Navigation -->
        <CampaignsNavigation
            v-if="selectedAccount && showCampaigns"
            :selectedAccount="selectedAccount"
            :campaigns="campaigns"
            :adSets="adSets"
            :ads="ads"
            :campaignsView="campaignsView"
            :searchTerm="campaignSearchTerm"
            :loadingCampaigns="loadingCampaigns"
            :loadingAdSets="loadingAdSets"
            :loadingAds="loadingAds"
            :filteredCampaigns="filteredCampaigns"
            :viewTitle="getViewTitle(selectedAccount)"
            :getStatusSeverity="getCampaignStatusSeverity"
            @load-campaigns="handleLoadCampaigns"
            @update:search-term="campaignSearchTerm = $event"
            @campaign-click="handleCampaignClick"
            @adset-click="handleAdSetClick"
            @go-back="goBack"
        />

        <!-- Rules Section -->
        <RulesSection
            v-if="selectedAccount"
            :selectedAccount="selectedAccount"
            :rules="rules"
            :loading="loading"
            :testingRuleId="testingRuleId"
            @create-rule="openCreateDialog"
            @test-rule="handleTestRule"
            @cancel-test="cancelTestRule"
            @view-logs="viewLogs"
            @edit-rule="editRule"
            @delete-rule="confirmDelete"
        />

        <!-- Ad Account Dialog -->
        <AdAccountDialog
            v-model="showAdAccountDialog"
            :editingAccount="editingAccount"
            :accountForm="accountForm"
            :connectionStatus="connectionStatus"
            :connectionLastChecked="connectionLastChecked"
            :testingConnection="testingConnection"
            :saving="savingAccount"
            @save="handleSaveAdAccount"
            @close="closeAccountDialog"
            @test-connection="testConnection"
        />

        <!-- Rule Builder Dialog -->
        <RuleBuilderDialog
            v-model="showCreateDialog"
            :editingRule="editingRule"
            :selectedAccountId="selectedAccount?.id"
            @save="handleSaveRuleData"
            @cancel="closeCreateDialog"
        />

        <!-- Logs Dialog -->
        <LogsDialog
            v-model="showLogsDialog"
            :logs="logs"
            :loading="loadingLogs"
            @show-details="showLogDetails"
            @download="downloadLogDetails"
            @delete="confirmDeleteLog"
        />

        <!-- Log Details Dialog -->
        <LogDetailsDialog v-model="showLogDetailsDialog" :logDetails="selectedLogDetails" />

        <ConfirmDialog />
        <Toast />
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";
import Toast from "primevue/toast";
import ConfirmDialog from "primevue/confirmdialog";

// Components
import AdAccountsSection from "@/components/meta-campaigns/AdAccountsSection.vue";
import CampaignsNavigation from "@/components/meta-campaigns/CampaignsNavigation.vue";
import RulesSection from "@/components/meta-campaigns/RulesSection.vue";
import AdAccountDialog from "@/components/meta-campaigns/dialogs/AdAccountDialog.vue";
import RuleBuilderDialog from "@/components/meta-campaigns/dialogs/RuleBuilderDialog.vue";
import LogsDialog from "@/components/meta-campaigns/dialogs/LogsDialog.vue";
import LogDetailsDialog from "@/components/meta-campaigns/dialogs/LogDetailsDialog.vue";

// Composables
import { useAdAccounts } from "@/composables/useAdAccounts";
import { useCampaigns } from "@/composables/useCampaigns";
import { useRules } from "@/composables/useRules";

const toast = useToast();

// Use composables
const {
    adAccounts,
    selectedAccount,
    loadingAccounts,
    savingAccount,
    testingConnection,
    connectionStatus,
    connectionLastChecked,
    showAdAccountDialog,
    editingAccount,
    accountForm,
    loadAdAccounts,
    loadDefaultAccount,
    selectAccount,
    openCreateAdAccountDialog,
    editAdAccount,
    closeAccountDialog,
    testConnection,
    saveAdAccount,
    confirmDeleteAccount,
} = useAdAccounts();

const {
    campaigns,
    campaignSearchTerm,
    adSets,
    ads,
    campaignsView,
    selectedCampaign,
    selectedAdSet,
    showCampaigns,
    loadingCampaigns,
    loadingAdSets,
    loadingAds,
    filteredCampaigns,
    getCampaignStatusSeverity,
    getViewTitle,
    loadCampaigns,
    onCampaignClick,
    loadAdSets,
    onAdSetClick,
    loadAds,
    goBack,
    resetCampaigns,
} = useCampaigns();

const {
    rules,
    allRules,
    loading,
    loadingLogs,
    saving,
    testingRuleId,
    showLogsDialog,
    showLogDetailsDialog,
    showCreateDialog,
    editingRule,
    logs,
    currentRuleForLogs,
    selectedLogDetails,
    loadAllRules,
    loadRules,
    getRulesCountForAccount,
    saveRule,
    confirmDelete,
    testRule,
    cancelTestRule,
    viewLogs,
    confirmDeleteLog,
    showLogDetails,
    downloadLogDetails,
    openCreateDialog,
    editRule,
    closeCreateDialog,
    handleSaveRule,
} = useRules();

// Polling interval
let rulesPollingInterval = null;

// Handlers
async function onAccountSelect(event) {
    selectAccount(event.data);
    // Reset campaigns when account changes
    resetCampaigns();
    // Load rules for the selected account
    if (event.data && event.data.id) {
        await loadRules(event.data.id);
    }
}

function handleLoadCampaigns() {
    if (selectedAccount.value) {
        loadCampaigns(selectedAccount.value.id);
    }
}


function handleCampaignClick(campaign) {
    if (selectedAccount.value) {
        onCampaignClick(campaign, selectedAccount.value.id);
    }
}

function handleAdSetClick(adSet) {
    if (selectedAccount.value) {
        onAdSetClick(adSet, selectedAccount.value.id);
    }
}

async function handleSaveAdAccount(formData) {
    // Update accountForm with formData
    Object.assign(accountForm.value, formData);
    await saveAdAccount();
    // Reload rules count if account was saved
    await loadAllRules();
}

async function handleTestRule(ruleId) {
    await testRule(ruleId, async () => {
        // Reload rules after test completes
        if (selectedAccount.value) {
            await loadRules(selectedAccount.value.id, true);
        }
    });
}

async function handleSaveRuleData(ruleData) {
    if (selectedAccount.value && selectedAccount.value.id) {
        const success = await handleSaveRule(ruleData, selectedAccount.value.id);
        if (success && selectedAccount.value.id) {
            // Reload rules to show the newly created/updated rule
            await loadRules(selectedAccount.value.id);
        }
    } else {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: "No account selected. Please select an account first.",
            life: 5000,
        });
    }
}

// Lifecycle
onMounted(async () => {
    try {
        await loadAdAccounts();
    } catch (error) {
        console.error("Failed to load ad accounts:", error);
    }

    try {
        await loadAllRules();
    } catch (error) {
        console.error("Failed to load all rules:", error);
    }

    try {
        const defaultAccount = await loadDefaultAccount();
        if (defaultAccount) {
            await loadRules(defaultAccount.id);
        }
    } catch (error) {
        // No default account yet - this is expected
        console.log("No default account found");
    }

    // Start polling for rules updates every 5 seconds
    rulesPollingInterval = setInterval(() => {
        if (selectedAccount.value) {
            loadRules(selectedAccount.value.id, true);
        }
        loadAllRules();
    }, 5000);
});

onUnmounted(() => {
    if (rulesPollingInterval) {
        clearInterval(rulesPollingInterval);
        rulesPollingInterval = null;
    }
});

// Watchers
watch(
    () => selectedAccount.value,
    async (newAccount, oldAccount) => {
        if (newAccount && newAccount.id) {
            await loadRules(newAccount.id);
        } else {
            rules.value = [];
        }
    },
    { immediate: false }
);
</script>

<style scoped>
.meta-campaigns {
    padding: 2rem;
}

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
}

.page-header h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
}

.header-actions {
    display: flex;
    gap: 1rem;
}

.campaigns-toggle-section {
    margin: 2rem 0;
}

.campaigns-toggle-button {
    width: 100%;
}
</style>
