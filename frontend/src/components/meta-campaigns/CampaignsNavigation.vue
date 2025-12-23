<template>
    <div class="campaigns-section">
        <div class="section-header">
            <div class="header-left">
                <Button
                    v-if="campaignsView !== 'campaigns'"
                    icon="pi pi-arrow-left"
                    label="Back"
                    severity="secondary"
                    outlined
                    @click="$emit('go-back')"
                    class="back-button"
                />
                <h2 :class="{ 'small-title': campaignsView !== 'campaigns' }">
                    <span class="view-prefix">{{ viewTitle.prefix }}</span>
                    {{ viewTitle.name }}
                </h2>
            </div>
            <div class="header-right">
                <Button
                    v-if="campaignsView === 'campaigns'"
                    label="Refresh"
                    icon="pi pi-refresh"
                    severity="secondary"
                    outlined
                    @click="$emit('load-campaigns')"
                    :loading="loadingCampaigns"
                    :disabled="loadingCampaigns"
                />
            </div>
        </div>

        <!-- Campaigns View -->
        <div v-if="campaignsView === 'campaigns'">
            <div v-if="!campaigns || campaigns.length === 0" class="empty-message">
                <p v-if="!loadingCampaigns">Click "Refresh" to load campaigns from Meta API</p>
                <p v-else>Loading campaigns...</p>
            </div>
            <div v-else>
                <div class="campaign-search-field" style="margin-bottom: 1rem">
                    <span class="p-input-icon-left" style="width: 100%">
                        <i class="pi pi-search" />
                        <InputText
                            :modelValue="searchTerm"
                            @update:modelValue="$emit('update:search-term', $event)"
                            placeholder="Search campaigns by ID or name..."
                            class="w-full"
                        />
                    </span>
                </div>
                <DataTable
                    :value="filteredCampaigns"
                    :loading="loadingCampaigns"
                    paginator
                    :rows="10"
                    :rowsPerPageOptions="[10, 20, 50]"
                    class="campaigns-table"
                    :rowHover="true"
                >
                    <Column field="id" header="ID" sortable />
                    <Column field="name" header="Name" sortable>
                        <template #body="slotProps">
                            <div class="clickable-row" @click.stop="$emit('campaign-click', slotProps.data)">
                                {{ slotProps.data.name }}
                                <i class="pi pi-chevron-right" style="margin-left: 0.5rem; color: #6b7280"></i>
                            </div>
                        </template>
                    </Column>
                    <Column field="status" header="Status" sortable>
                        <template #body="slotProps">
                            <Tag :value="slotProps.data.status" :severity="getStatusSeverity(slotProps.data.status)" />
                        </template>
                    </Column>
                    <Column field="effective_status" header="Effective Status" sortable>
                        <template #body="slotProps">
                            <Tag
                                :value="slotProps.data.effective_status"
                                :severity="getStatusSeverity(slotProps.data.effective_status)"
                            />
                        </template>
                    </Column>
                </DataTable>
            </div>
        </div>

        <!-- Ad Sets View -->
        <div v-else-if="campaignsView === 'adsets'">
            <div v-if="!adSets || adSets.length === 0" class="empty-message">
                <p v-if="!loadingAdSets">No ad sets found for this campaign</p>
                <p v-else>Loading ad sets...</p>
            </div>
            <DataTable
                v-else
                :value="adSets"
                :loading="loadingAdSets"
                paginator
                :rows="10"
                :rowsPerPageOptions="[10, 20, 50]"
                class="campaigns-table"
                @row-click="(e) => $emit('adset-click', e.data)"
                :rowHover="true"
            >
                <Column field="id" header="ID" sortable />
                <Column field="name" header="Name" sortable>
                    <template #body="slotProps">
                        <div class="clickable-row" @click.stop="$emit('adset-click', slotProps.data)">
                            {{ slotProps.data.name }}
                            <i class="pi pi-chevron-right" style="margin-left: 0.5rem; color: #6b7280"></i>
                        </div>
                    </template>
                </Column>
                <Column field="status" header="Status" sortable>
                    <template #body="slotProps">
                        <Tag :value="slotProps.data.status" :severity="getStatusSeverity(slotProps.data.status)" />
                    </template>
                </Column>
                <Column field="effective_status" header="Effective Status" sortable>
                    <template #body="slotProps">
                        <Tag
                            :value="slotProps.data.effective_status"
                            :severity="getStatusSeverity(slotProps.data.effective_status)"
                        />
                    </template>
                </Column>
            </DataTable>
        </div>

        <!-- Ads View -->
        <div v-else-if="campaignsView === 'ads'">
            <div v-if="!ads || ads.length === 0" class="empty-message">
                <p v-if="!loadingAds">No ads found for this ad set</p>
                <p v-else>Loading ads...</p>
            </div>
            <DataTable
                v-else
                :value="ads"
                :loading="loadingAds"
                paginator
                :rows="10"
                :rowsPerPageOptions="[10, 20, 50]"
                class="campaigns-table"
            >
                <Column field="id" header="ID" sortable />
                <Column field="name" header="Name" sortable />
                <Column field="status" header="Status" sortable>
                    <template #body="slotProps">
                        <Tag :value="slotProps.data.status" :severity="getStatusSeverity(slotProps.data.status)" />
                    </template>
                </Column>
                <Column field="effective_status" header="Effective Status" sortable>
                    <template #body="slotProps">
                        <Tag
                            :value="slotProps.data.effective_status"
                            :severity="getStatusSeverity(slotProps.data.effective_status)"
                        />
                    </template>
                </Column>
            </DataTable>
        </div>
    </div>
</template>

<script setup>
import Button from "primevue/button";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Tag from "primevue/tag";
import InputText from "primevue/inputtext";

defineProps({
    selectedAccount: {
        type: Object,
        default: null,
    },
    showCampaigns: {
        type: Boolean,
        default: false,
    },
    campaignsView: {
        type: String,
        default: "campaigns",
    },
    campaigns: {
        type: Array,
        default: () => [],
    },
    adSets: {
        type: Array,
        default: () => [],
    },
    ads: {
        type: Array,
        default: () => [],
    },
    searchTerm: {
        type: String,
        default: "",
    },
    filteredCampaigns: {
        type: Array,
        default: () => [],
    },
    loadingCampaigns: {
        type: Boolean,
        default: false,
    },
    loadingAdSets: {
        type: Boolean,
        default: false,
    },
    loadingAds: {
        type: Boolean,
        default: false,
    },
    viewTitle: {
        type: Object,
        required: true,
    },
    getStatusSeverity: {
        type: Function,
        required: true,
    },
});

defineEmits(["go-back", "load-campaigns", "update:search-term", "campaign-click", "adset-click"]);
</script>

<style scoped>
.campaigns-section {
    margin-top: 2rem;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.view-prefix {
    color: #6b7280;
    font-weight: normal;
}

h2.small-title {
    font-size: 1rem;
    font-weight: 500;
}

.empty-message {
    padding: 2rem;
    text-align: center;
    color: #6b7280;
}

.clickable-row {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: #3b82f6;
}

.clickable-row:hover {
    text-decoration: underline;
}

.campaign-search-field {
    width: 100%;
}

.campaign-search-field .p-input-icon-left {
    position: relative;
    display: block;
    width: 100%;
}

.campaign-search-field .p-input-icon-left i {
    position: absolute;
    left: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    color: #6b7280;
    z-index: 1;
}

.campaign-search-field .p-input-icon-left .p-inputtext {
    padding-left: 2.5rem;
}
</style>
