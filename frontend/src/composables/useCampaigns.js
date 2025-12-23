import { ref, computed } from "vue";
import { useToast } from "primevue/usetoast";
import { getAdAccountCampaigns, getCampaignAdSets, getAdSetAds } from "@/api/adAccountsApi";

export function useCampaigns() {
    const toast = useToast();

    const campaigns = ref([]);
    const campaignSearchTerm = ref("");
    const adSets = ref([]);
    const ads = ref([]);
    const campaignsView = ref("campaigns"); // 'campaigns', 'adsets', 'ads'
    const selectedCampaign = ref(null);
    const selectedAdSet = ref(null);
    const showCampaigns = ref(false);

    const loadingCampaigns = ref(false);
    const loadingAdSets = ref(false);
    const loadingAds = ref(false);

    const filteredCampaigns = computed(() => {
        if (!campaignSearchTerm.value || campaignSearchTerm.value.trim() === "") {
            return campaigns.value;
        }
        const searchTerm = campaignSearchTerm.value.toLowerCase().trim();
        return campaigns.value.filter((campaign) => {
            const id = String(campaign.id || "").toLowerCase();
            const name = String(campaign.name || "").toLowerCase();
            return id.includes(searchTerm) || name.includes(searchTerm);
        });
    });

    function getCampaignStatusSeverity(status) {
        if (!status) return "secondary";
        const upperStatus = status.toUpperCase();
        if (upperStatus === "ACTIVE") return "success";
        if (upperStatus === "PAUSED") return "warning";
        if (upperStatus === "DELETED" || upperStatus === "ARCHIVED") return "danger";
        return "secondary";
    }

    function getViewTitle(selectedAccount) {
        if (campaignsView.value === "adsets") {
            return {
                prefix: "Ad Sets for",
                name: selectedCampaign.value?.name || "Campaign",
            };
        } else if (campaignsView.value === "ads") {
            return {
                prefix: "Ads for",
                name: selectedAdSet.value?.name || "Ad Set",
            };
        }
        return {
            prefix: "Campaigns for",
            name: selectedAccount?.name || "",
        };
    }

    async function loadCampaigns(accountId) {
        if (!accountId) {
            toast.add({
                severity: "warn",
                summary: "No Account Selected",
                detail: "Please select an ad account first",
                life: 3000,
            });
            return;
        }

        loadingCampaigns.value = true;
        try {
            const response = await getAdAccountCampaigns(accountId);
            campaigns.value = response.data || [];
            toast.add({
                severity: "success",
                summary: "Campaigns Loaded",
                detail: `Loaded ${campaigns.value.length} campaign(s)`,
                life: 3000,
            });
        } catch (error) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to load campaigns",
                life: 5000,
            });
            campaigns.value = [];
        } finally {
            loadingCampaigns.value = false;
        }
    }

    function onCampaignClick(campaign, accountId) {
        selectedCampaign.value = campaign;
        campaignsView.value = "adsets";
        loadAdSets(accountId, campaign.id);
    }

    async function loadAdSets(accountId, campaignId) {
        if (!accountId) return;

        loadingAdSets.value = true;
        try {
            const response = await getCampaignAdSets(accountId, campaignId);
            adSets.value = response.data || [];
        } catch (error) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to load ad sets",
                life: 5000,
            });
            adSets.value = [];
        } finally {
            loadingAdSets.value = false;
        }
    }

    function onAdSetClick(adSet, accountId) {
        selectedAdSet.value = adSet;
        campaignsView.value = "ads";
        loadAds(accountId, adSet.id);
    }

    async function loadAds(accountId, adsetId) {
        if (!accountId) return;

        loadingAds.value = true;
        try {
            const response = await getAdSetAds(accountId, adsetId);
            ads.value = response.data || [];
        } catch (error) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to load ads",
                life: 5000,
            });
            ads.value = [];
        } finally {
            loadingAds.value = false;
        }
    }

    function goBack() {
        if (campaignsView.value === "ads") {
            // Go back to ad sets
            campaignsView.value = "adsets";
            ads.value = [];
            selectedAdSet.value = null;
        } else if (campaignsView.value === "adsets") {
            // Go back to campaigns
            campaignsView.value = "campaigns";
            adSets.value = [];
            selectedCampaign.value = null;
        }
    }

    function resetCampaigns() {
        campaigns.value = [];
        adSets.value = [];
        ads.value = [];
        campaignsView.value = "campaigns";
        selectedCampaign.value = null;
        selectedAdSet.value = null;
        showCampaigns.value = false;
        campaignSearchTerm.value = "";
    }

    return {
        // State
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
        // Computed
        filteredCampaigns,
        // Methods
        getCampaignStatusSeverity,
        getViewTitle,
        loadCampaigns,
        onCampaignClick,
        loadAdSets,
        onAdSetClick,
        loadAds,
        goBack,
        resetCampaigns,
    };
}
