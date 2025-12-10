<template>
    <div class="meta-campaigns">
        <div class="page-header">
            <h1>Meta Campaigns</h1>
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
        <div class="ad-accounts-section">
            <h2>Ad Accounts</h2>
            <DataTable
                :value="adAccounts"
                :loading="loadingAccounts"
                :selectionMode="'single'"
                v-model:selection="selectedAccount"
                class="accounts-table"
                @row-select="onAccountSelect"
            >
                <Column selectionMode="single" headerStyle="width: 3rem"></Column>
                <Column field="name" header="Name" sortable />
                <Column field="description" header="Description" />
                <Column field="is_default" header="Default">
                    <template #body="slotProps">
                        <Tag v-if="slotProps.data.is_default" value="Default" severity="success" />
                    </template>
                </Column>
                <Column header="Actions">
                    <template #body="slotProps">
                        <div class="action-buttons">
                            <Button
                                icon="pi pi-pencil"
                                severity="warning"
                                text
                                rounded
                                @click="editAdAccount(slotProps.data)"
                                v-tooltip.top="'Edit'"
                            />
                            <Button
                                icon="pi pi-trash"
                                severity="danger"
                                text
                                rounded
                                @click="confirmDeleteAccount(slotProps.data)"
                                v-tooltip.top="'Delete'"
                            />
                        </div>
                    </template>
                </Column>
            </DataTable>
        </div>

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

        <!-- Campaigns Section (shown when account is selected and toggle is on) -->
        <div v-if="selectedAccount && showCampaigns" class="campaigns-section">
            <div class="section-header">
                <div class="header-left">
                    <Button
                        v-if="campaignsView !== 'campaigns'"
                        icon="pi pi-arrow-left"
                        label="Back"
                        severity="secondary"
                        outlined
                        @click="goBack"
                        class="back-button"
                    />
                    <h2>
                        <span class="view-prefix">{{ getViewTitle().prefix }}</span>
                        {{ getViewTitle().name }}
                    </h2>
                </div>
                <div class="header-right">
                    <Button
                        v-if="campaignsView === 'campaigns'"
                        label="Refresh"
                        icon="pi pi-refresh"
                        severity="secondary"
                        outlined
                        @click="loadCampaigns"
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
                <DataTable
                    v-else
                    :value="campaigns"
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
                            <div class="clickable-row" @click.stop="onCampaignClick({ data: slotProps.data })">
                                {{ slotProps.data.name }}
                                <i class="pi pi-chevron-right" style="margin-left: 0.5rem; color: #6b7280;"></i>
                            </div>
                        </template>
                    </Column>
                    <Column field="status" header="Status" sortable>
                        <template #body="slotProps">
                            <Tag
                                :value="slotProps.data.status"
                                :severity="getCampaignStatusSeverity(slotProps.data.status)"
                            />
                        </template>
                    </Column>
                    <Column field="effective_status" header="Effective Status" sortable>
                        <template #body="slotProps">
                            <Tag
                                :value="slotProps.data.effective_status"
                                :severity="getCampaignStatusSeverity(slotProps.data.effective_status)"
                            />
                        </template>
                    </Column>
                </DataTable>
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
                    @row-click="onAdSetClick"
                    :rowHover="true"
                >
                    <Column field="id" header="ID" sortable />
                    <Column field="name" header="Name" sortable>
                        <template #body="slotProps">
                            <div class="clickable-row" @click.stop="onAdSetClick({ data: slotProps.data })">
                                {{ slotProps.data.name }}
                                <i class="pi pi-chevron-right" style="margin-left: 0.5rem; color: #6b7280;"></i>
                            </div>
                        </template>
                    </Column>
                    <Column field="status" header="Status" sortable>
                        <template #body="slotProps">
                            <Tag
                                :value="slotProps.data.status"
                                :severity="getCampaignStatusSeverity(slotProps.data.status)"
                            />
                        </template>
                    </Column>
                    <Column field="effective_status" header="Effective Status" sortable>
                        <template #body="slotProps">
                            <Tag
                                :value="slotProps.data.effective_status"
                                :severity="getCampaignStatusSeverity(slotProps.data.effective_status)"
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
                            <Tag
                                :value="slotProps.data.status"
                                :severity="getCampaignStatusSeverity(slotProps.data.status)"
                            />
                        </template>
                    </Column>
                    <Column field="effective_status" header="Effective Status" sortable>
                        <template #body="slotProps">
                            <Tag
                                :value="slotProps.data.effective_status"
                                :severity="getCampaignStatusSeverity(slotProps.data.effective_status)"
                            />
                        </template>
                    </Column>
                </DataTable>
            </div>
        </div>

        <!-- Rules Section (shown when account is selected) -->
        <div v-if="selectedAccount" class="rules-section">
            <div class="section-header">
                <h2>Rules for {{ selectedAccount.name }}</h2>
                <Button label="Create Rule" icon="pi pi-plus" @click="openCreateDialog" />
            </div>
            <DataTable
                :value="rules"
                :loading="loading"
                paginator
                :rows="10"
                :rowsPerPageOptions="[10, 20, 50]"
                class="rules-table"
            >
                <Column field="name" header="Name" sortable>
                    <template #body="slotProps">
                        <div class="name-column">
                            <div class="name-text">{{ slotProps.data.name }}</div>
                            <div v-if="slotProps.data.description" class="description-text">
                                {{ slotProps.data.description }}
                            </div>
                        </div>
                    </template>
                </Column>
                <Column field="schedule_cron" header="Schedule">
                    <template #body="slotProps">
                        {{ formatSchedule(slotProps.data.schedule_cron) }}
                    </template>
                </Column>
                <Column field="enabled" header="Status">
                    <template #body="slotProps">
                        <Tag
                            :value="slotProps.data.enabled ? 'Enabled' : 'Disabled'"
                            :severity="slotProps.data.enabled ? 'success' : 'secondary'"
                        />
                    </template>
                </Column>
                <Column field="last_run_at" header="Last Run">
                    <template #body="slotProps">
                        <span class="run-time-text">
                            {{ formatDateWithTimezone(slotProps.data.last_run_at, slotProps.data.schedule_cron) }}
                        </span>
                    </template>
                </Column>
                <Column field="next_run_at" header="Next Run">
                    <template #body="slotProps">
                        <span v-if="slotProps.data.schedule_cron" class="run-time-text">
                            {{ formatDateWithTimezone(slotProps.data.next_run_at, slotProps.data.schedule_cron) }}
                        </span>
                        <span v-else class="text-secondary run-time-text">N/A</span>
                    </template>
                </Column>
                <Column header="Actions">
                    <template #body="slotProps">
                        <div class="action-buttons">
                            <Button
                                :icon="testingRuleId === slotProps.data.id ? 'pi pi-spin pi-spinner' : 'pi pi-play'"
                                severity="success"
                                text
                                rounded
                                :loading="testingRuleId === slotProps.data.id"
                                :disabled="testingRuleId === slotProps.data.id"
                                @click="testRule(slotProps.data.id)"
                                v-tooltip.top="'Test Rule'"
                            />
                            <Button
                                icon="pi pi-list"
                                severity="info"
                                text
                                rounded
                                @click="viewLogs(slotProps.data.id)"
                                v-tooltip.top="'View Logs'"
                            />
                            <Button
                                icon="pi pi-pencil"
                                severity="warning"
                                text
                                rounded
                                @click="editRule(slotProps.data)"
                                v-tooltip.top="'Edit'"
                            />
                            <Button
                                icon="pi pi-trash"
                                severity="danger"
                                text
                                rounded
                                @click="confirmDelete(slotProps.data)"
                                v-tooltip.top="'Delete'"
                            />
                        </div>
                    </template>
                </Column>
            </DataTable>
        </div>

        <!-- Ad Account Create/Edit Dialog -->
        <Dialog
            v-model:visible="showAdAccountDialog"
            :header="editingAccount ? 'Edit Ad Account' : 'Create Ad Account'"
            :modal="true"
            :style="{ width: '600px' }"
        >
            <div class="form-content">
                <div class="field">
                    <label>Name *</label>
                    <InputText v-model="accountForm.name" class="w-full" />
                </div>
                <div class="field">
                    <label>Description</label>
                    <Textarea v-model="accountForm.description" class="w-full" rows="3" />
                </div>
                <div class="field">
                    <label>Meta Account ID</label>
                    <InputText v-model="accountForm.meta_account_id" class="w-full" />
                </div>
                <div class="field">
                    <label>Meta Access Token</label>
                    <Password
                        v-model="accountForm.meta_access_token"
                        :feedback="false"
                        toggleMask
                        class="w-full access-token-field"
                        :inputClass="'w-full'"
                    />
                </div>
                <div class="field">
                    <label>Slack Webhook URL</label>
                    <InputText
                        v-model="accountForm.slack_webhook_url"
                        class="w-full"
                        placeholder="https://hooks.slack.com/services/..."
                    />
                    <small class="p-text-secondary"
                        >Enter your Slack webhook URL to receive notifications when rules execute actions</small
                    >
                </div>
                <div class="field checkbox-field">
                    <div class="checkbox-container">
                        <Checkbox v-model="accountForm.is_default" inputId="is_default" :binary="true" />
                        <label for="is_default" class="checkbox-label">Set as Default</label>
                    </div>
                </div>
                <!-- Connection Status (only show when editing) -->
                <div v-if="editingAccount" class="field">
                    <label>Connection Status</label>
                    <div class="connection-status-container">
                        <div class="connection-status-info">
                            <i
                                v-if="connectionStatus === true"
                                class="pi pi-check-circle connection-status-icon success"
                            ></i>
                            <i
                                v-else-if="connectionStatus === false"
                                class="pi pi-times-circle connection-status-icon error"
                            ></i>
                            <i
                                v-else
                                class="pi pi-question-circle connection-status-icon unknown"
                            ></i>
                            <span class="connection-status-text">
                                {{ connectionStatus === true ? 'Active' : connectionStatus === false ? 'Failed' : 'Not Tested' }}
                            </span>
                        </div>
                        <div v-if="connectionLastChecked" class="connection-last-checked">
                            <small class="p-text-secondary">
                                Last checked: {{ formatDate(connectionLastChecked) }}
                            </small>
                        </div>
                    </div>
                    <Button
                        label="Test Connection"
                        icon="pi pi-refresh"
                        severity="secondary"
                        outlined
                        @click="testConnection"
                        :loading="testingConnection"
                        :disabled="testingConnection"
                        class="mt-2"
                    />
                </div>
            </div>
            <template #footer>
                <Button label="Cancel" severity="secondary" @click="closeAccountDialog" />
                <Button
                    :label="editingAccount ? 'Update' : 'Create'"
                    @click="saveAdAccount"
                    :loading="savingAccount"
                />
            </template>
        </Dialog>

        <!-- Create/Edit Rule Dialog -->
        <Dialog
            v-model:visible="showCreateDialog"
            :header="editingRule ? 'Edit Rule' : 'Create Rule'"
            :modal="true"
            :style="{ maxWidth: '900px', width: '90vw', maxHeight: '90vh' }"
            class="rule-builder-dialog"
        >
            <div class="form-content">
                <!-- SECTION 1: BASIC INFO -->
                <div class="form-section">
                    <h3 class="section-title">1. Basic Info</h3>
                    <div class="field">
                        <label>Rule Name *</label>
                        <InputText v-model="ruleForm.name" class="w-full" :class="{ 'p-invalid': formErrors.name }" />
                        <small v-if="formErrors.name" class="p-error">{{ formErrors.name }}</small>
                    </div>
                    <div class="field">
                        <label>Description</label>
                        <Textarea v-model="ruleForm.description" class="w-full" rows="3" />
                    </div>
                    <div v-if="ruleForm.ruleLevel" class="field">
                        <div class="flex align-items-center gap-2">
                            <InputSwitch v-model="ruleForm.enabled" inputId="enabled" />
                            <label for="enabled" class="field-label">Enabled</label>
                        </div>
                    </div>
                </div>

                <!-- SECTION 2: LEVEL AND SCOPE -->
                <div class="form-section">
                    <h3 class="section-title">2. Level and Scope</h3>

                    <!-- 2A: Rule Level -->
                    <div class="subsection">
                        <h4 class="subsection-title">2A. Rule Level</h4>
                        <div class="field">
                            <label>Rule Level *</label>
                            <Select
                                v-model="ruleForm.ruleLevel"
                                :options="ruleLevelOptions"
                                optionLabel="label"
                                optionValue="value"
                                placeholder="Select rule level"
                                class="w-full"
                                :class="{ 'p-invalid': formErrors.ruleLevel }"
                                @change="onRuleLevelChange"
                            />
                            <small v-if="formErrors.ruleLevel" class="p-error">{{ formErrors.ruleLevel }}</small>
                        </div>
                    </div>

                    <!-- 2B: Scope Filters -->
                    <div class="subsection">
                        <h4 class="subsection-title">2B. Scope Filters</h4>
                        <div v-if="ruleForm.scopeFilters.length === 0" class="empty-scope">
                            <p>No scope filters defined.</p>
                        </div>
                        <div v-else class="scope-filters-list">
                            <div v-for="(scope, index) in ruleForm.scopeFilters" :key="index" class="scope-filter-item">
                                <div class="scope-filter-header">
                                    <strong>{{ getScopeTypeLabel(scope.type) }}</strong>
                                    <Button
                                        icon="pi pi-times"
                                        severity="danger"
                                        text
                                        rounded
                                        size="small"
                                        @click="removeScopeFilter(index)"
                                        v-tooltip.top="'Remove'"
                                    />
                                </div>
                                <div class="scope-filter-content">
                                    <!-- Name contains -->
                                    <div v-if="scope.type === 'name_contains'" class="field">
                                        <label>Keywords *</label>
                                        <Chips
                                            v-model="scope.value"
                                            placeholder="Type keyword and press Enter to add"
                                            class="w-full"
                                            :class="{
                                                'p-invalid':
                                                    formErrors.scopeFilters &&
                                                    (!Array.isArray(scope.value) || scope.value.length === 0),
                                            }"
                                            @add="
                                                () => {
                                                    formErrors.scopeFilters = '';
                                                }
                                            "
                                            @remove="() => {}"
                                        />
                                        <small
                                            v-if="
                                                formErrors.scopeFilters &&
                                                (!Array.isArray(scope.value) || scope.value.length === 0)
                                            "
                                            class="p-error"
                                        >
                                            Please add at least one keyword by typing and pressing Enter
                                        </small>
                                        <small v-else class="p-text-secondary"
                                            >Type a keyword and press Enter to add it</small
                                        >
                                        <small
                                            v-if="scope.value && Array.isArray(scope.value) && scope.value.length > 0"
                                            class="p-text-secondary mt-1 block"
                                        >
                                            Added keywords ({{ scope.value.length }}): {{ scope.value.join(", ") }}
                                        </small>
                                    </div>
                                    <!-- IDs -->
                                    <div v-else-if="scope.type === 'ids'" class="field">
                                        <label
                                            >{{
                                                ruleForm.ruleLevel === "ad"
                                                    ? "Ad ID"
                                                    : ruleForm.ruleLevel === "ad_set"
                                                    ? "Ad Set ID"
                                                    : "IDs"
                                            }}
                                            *</label
                                        >
                                        <Chips
                                            v-model="scope.value"
                                            placeholder="Type ID and press Enter to add"
                                            class="w-full"
                                            :class="{
                                                'p-invalid':
                                                    formErrors.scopeFilters &&
                                                    (!Array.isArray(scope.value) || scope.value.length === 0),
                                            }"
                                            @add="
                                                () => {
                                                    formErrors.scopeFilters = '';
                                                }
                                            "
                                            @remove="() => {}"
                                        />
                                        <small
                                            v-if="
                                                formErrors.scopeFilters &&
                                                (!Array.isArray(scope.value) || scope.value.length === 0)
                                            "
                                            class="p-error"
                                        >
                                            Please add at least one ID by typing and pressing Enter
                                        </small>
                                        <small v-else class="p-text-secondary"
                                            >Type an ID and press Enter to add it</small
                                        >
                                        <small
                                            v-if="scope.value && Array.isArray(scope.value) && scope.value.length > 0"
                                            class="p-text-secondary mt-1 block"
                                        >
                                            Added IDs ({{ scope.value.length }}): {{ scope.value.join(", ") }}
                                        </small>
                                    </div>
                                    <!-- Campaign Name contains -->
                                    <div v-else-if="scope.type === 'campaign_name_contains'" class="field">
                                        <label>Keywords *</label>
                                        <Chips
                                            v-model="scope.value"
                                            placeholder="Type keyword and press Enter to add"
                                            class="w-full"
                                            :class="{
                                                'p-invalid':
                                                    formErrors.scopeFilters &&
                                                    (!Array.isArray(scope.value) || scope.value.length === 0),
                                            }"
                                            @add="
                                                () => {
                                                    formErrors.scopeFilters = '';
                                                }
                                            "
                                            @remove="() => {}"
                                        />
                                        <small
                                            v-if="
                                                formErrors.scopeFilters &&
                                                (!Array.isArray(scope.value) || scope.value.length === 0)
                                            "
                                            class="p-error"
                                        >
                                            Please add at least one keyword by typing and pressing Enter
                                        </small>
                                        <small v-else class="p-text-secondary"
                                            >Type a keyword and press Enter to add it</small
                                        >
                                        <small
                                            v-if="scope.value && Array.isArray(scope.value) && scope.value.length > 0"
                                            class="p-text-secondary mt-1 block"
                                        >
                                            Added keywords ({{ scope.value.length }}): {{ scope.value.join(", ") }}
                                        </small>
                                    </div>
                                    <!-- Campaign IDs -->
                                    <div v-else-if="scope.type === 'campaign_ids'" class="field">
                                        <label>Campaign IDs *</label>
                                        <Chips
                                            v-model="scope.value"
                                            placeholder="Type campaign ID and press Enter to add"
                                            class="w-full"
                                            :class="{
                                                'p-invalid':
                                                    formErrors.scopeFilters &&
                                                    (!Array.isArray(scope.value) || scope.value.length === 0),
                                            }"
                                            @add="
                                                () => {
                                                    formErrors.scopeFilters = '';
                                                }
                                            "
                                            @remove="() => {}"
                                        />
                                        <small
                                            v-if="
                                                formErrors.scopeFilters &&
                                                (!Array.isArray(scope.value) || scope.value.length === 0)
                                            "
                                            class="p-error"
                                        >
                                            Please add at least one campaign ID by typing and pressing Enter
                                        </small>
                                        <small v-else class="p-text-secondary"
                                            >Type a campaign ID and press Enter to add it</small
                                        >
                                        <small
                                            v-if="scope.value && Array.isArray(scope.value) && scope.value.length > 0"
                                            class="p-text-secondary mt-1 block"
                                        >
                                            Added campaign IDs ({{ scope.value.length }}): {{ scope.value.join(", ") }}
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="field mt-3">
                            <Button
                                label="Add Scope"
                                icon="pi pi-plus"
                                severity="secondary"
                                outlined
                                @click="showAddScopeDialog = true"
                                :disabled="availableScopeTypes.length === 0"
                            />
                        </div>
                    </div>
                </div>

                <!-- SECTION 3: TIME RANGE -->
                <div v-if="ruleForm.ruleLevel" class="form-section">
                    <h3 class="section-title">3. Time Range (Data Window)</h3>
                    <div class="field">
                        <label>Time Unit *</label>
                        <Select
                            v-model="ruleForm.timeRangeUnit"
                            :options="timeRangeUnitOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Select time unit"
                            class="w-full"
                            :class="{ 'p-invalid': formErrors.timeRangeUnit }"
                        />
                        <small v-if="formErrors.timeRangeUnit" class="p-error">{{ formErrors.timeRangeUnit }}</small>
                    </div>
                    <div class="field">
                        <label>Amount *</label>
                        <InputNumber
                            v-model="ruleForm.timeRangeAmount"
                            :min="1"
                            placeholder="Enter amount"
                            class="w-full"
                            :class="{ 'p-invalid': formErrors.timeRangeAmount }"
                        />
                        <small v-if="formErrors.timeRangeAmount" class="p-error">{{
                            formErrors.timeRangeAmount
                        }}</small>
                    </div>
                    <div class="field">
                        <div class="flex align-items-center gap-2">
                            <InputSwitch
                                v-model="ruleForm.excludeToday"
                                inputId="excludeToday"
                                :disabled="ruleForm.timeRangeUnit === 'minutes' || ruleForm.timeRangeUnit === 'hours'"
                            />
                            <label for="excludeToday" class="field-label">Exclude today</label>
                        </div>
                        <small
                            class="p-text-secondary"
                            v-if="ruleForm.timeRangeUnit === 'minutes' || ruleForm.timeRangeUnit === 'hours'"
                        >
                            (No effect for minutes or hours)
                        </small>
                    </div>
                </div>

                <!-- SECTION 4: CONDITIONS -->
                <div v-if="ruleForm.ruleLevel" class="form-section">
                    <h3 class="section-title">4. Conditions</h3>
                    <div v-if="ruleForm.conditions.length === 0" class="empty-message">
                        <p>No conditions defined. Click "Add Condition" to add one.</p>
                    </div>
                    <div v-else class="conditions-list">
                        <div v-for="(condition, index) in ruleForm.conditions" :key="index" class="condition-item">
                            <div class="condition-header">
                                <strong>Condition {{ index + 1 }}</strong>
                                <Button
                                    icon="pi pi-times"
                                    severity="danger"
                                    text
                                    rounded
                                    size="small"
                                    @click="removeCondition(index)"
                                    v-tooltip.top="'Remove'"
                                />
                            </div>
                            <div class="condition-fields">
                                <div class="field">
                                    <label>Field *</label>
                                    <Select
                                        v-model="condition.field"
                                        :options="availableConditionFields"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select field"
                                        class="w-full"
                                        @change="onConditionFieldChange(index)"
                                    />
                                </div>
                                <div class="field">
                                    <label>Operator *</label>
                                    <Select
                                        v-model="condition.operator"
                                        :options="operatorOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select operator"
                                        class="w-full"
                                    />
                                </div>
                                <div class="field">
                                    <label>Value *</label>
                                    <Select
                                        v-if="condition.field === 'status' || condition.field === 'campaign_status'"
                                        v-model="condition.value"
                                        :options="statusOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select status"
                                        class="w-full"
                                    />
                                    <InputNumber
                                        v-else-if="isNumericField(condition.field)"
                                        v-model="condition.value"
                                        :min="0"
                                        :step="0.01"
                                        placeholder="Enter value"
                                        class="w-full"
                                    />
                                    <InputText
                                        v-else
                                        v-model="condition.value"
                                        :placeholder="getValuePlaceholder(condition.field)"
                                        class="w-full"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="field mt-3">
                        <Button
                            label="Add Condition"
                            icon="pi pi-plus"
                            severity="secondary"
                            outlined
                            @click="addCondition"
                            :disabled="!ruleForm.ruleLevel"
                        />
                    </div>
                </div>

                <!-- SECTION 5: ACTIONS -->
                <div v-if="ruleForm.ruleLevel" class="form-section">
                    <h3 class="section-title">5. Actions</h3>
                    <div v-if="ruleForm.actions.length === 0" class="empty-message">
                        <p>No actions defined. Click "Add Action" to add one.</p>
                    </div>
                    <div v-else class="actions-list">
                        <div v-for="(action, index) in ruleForm.actions" :key="index" class="action-item">
                            <div class="action-header">
                                <strong>Action {{ index + 1 }}</strong>
                                <Button
                                    icon="pi pi-times"
                                    severity="danger"
                                    text
                                    rounded
                                    size="small"
                                    @click="removeAction(index)"
                                    v-tooltip.top="'Remove'"
                                />
                            </div>
                            <div class="action-fields">
                                <div class="field">
                                    <label>Action Type *</label>
                                    <Select
                                        v-model="action.type"
                                        :options="availableActionTypes"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select action type"
                                        class="w-full"
                                        @change="onActionTypeChange(index)"
                                    />
                                </div>
                                <!-- Set Status action fields -->
                                <div v-if="action.type === 'set_status'" class="field">
                                    <label>Status *</label>
                                    <Select
                                        v-model="action.status"
                                        :options="statusOptions"
                                        optionLabel="label"
                                        optionValue="value"
                                        placeholder="Select status"
                                        class="w-full"
                                    />
                                </div>
                                <!-- Send Notification action - no additional fields, just notification -->
                                <div v-if="action.type === 'send_notification'" class="field">
                                    <small class="p-text-secondary"
                                        >This action will only send a Slack notification without making any changes to
                                        the item.</small
                                    >
                                </div>
                                <!-- Adjust Daily Budget action fields -->
                                <template v-if="action.type === 'adjust_daily_budget'">
                                    <div class="field">
                                        <label>Direction *</label>
                                        <Select
                                            v-model="action.direction"
                                            :options="budgetDirectionOptions"
                                            optionLabel="label"
                                            optionValue="value"
                                            placeholder="Select direction"
                                            class="w-full"
                                        />
                                    </div>
                                    <div class="field">
                                        <label>Percent Value *</label>
                                        <InputNumber
                                            v-model="action.percent"
                                            :min="0"
                                            :max="100"
                                            :step="0.01"
                                            placeholder="Enter percentage"
                                            class="w-full"
                                        />
                                    </div>
                                    <div class="field">
                                        <label>Minimum Cap</label>
                                        <InputNumber
                                            v-model="action.minCap"
                                            :min="0"
                                            :step="0.01"
                                            placeholder="Enter minimum cap"
                                            class="w-full"
                                        />
                                    </div>
                                    <div class="field">
                                        <label>Maximum Cap</label>
                                        <InputNumber
                                            v-model="action.maxCap"
                                            :min="0"
                                            :step="0.01"
                                            placeholder="Enter maximum cap"
                                            class="w-full"
                                        />
                                    </div>
                                </template>
                            </div>
                            <!-- Send Slack Notification checkbox - separate row at bottom -->
                            <!-- For send_notification action, always show as enabled (but still show checkbox for consistency) -->
                            <div class="action-slack-notification">
                                <div class="flex align-items-center gap-2">
                                    <Checkbox
                                        v-model="action.sendSlackNotification"
                                        :binary="true"
                                        :inputId="`slack-notification-${index}`"
                                        :disabled="action.type === 'send_notification'"
                                    />
                                    <label :for="`slack-notification-${index}`" class="slack-notification-label"
                                        >Send slack notification</label
                                    >
                                    <small v-if="action.type === 'send_notification'" class="p-text-secondary ml-2"
                                        >(always enabled for notification actions)</small
                                    >
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="field mt-3">
                        <Button
                            label="Add Action"
                            icon="pi pi-plus"
                            severity="secondary"
                            outlined
                            @click="addAction"
                            :disabled="!ruleForm.ruleLevel"
                        />
                    </div>
                </div>

                <!-- SECTION 6: EXECUTION SCHEDULE -->
                <div v-if="ruleForm.ruleLevel" class="form-section scheduling-section">
                    <h3 class="section-title">6. Execution Schedule</h3>

                    <div class="field">
                        <label>Period</label>
                        <Select
                            v-model="ruleForm.schedulePeriod"
                            :options="periodOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Select period (optional)"
                            class="w-full"
                            :class="{ 'p-invalid': scheduleFormErrors.period }"
                            @change="onSchedulePeriodChange"
                        />
                        <small v-if="scheduleFormErrors.period" class="p-error">{{ scheduleFormErrors.period }}</small>
                    </div>

                    <div
                        class="field"
                        v-if="
                            ruleForm.schedulePeriod &&
                            ruleForm.schedulePeriod !== 'none' &&
                            ruleForm.schedulePeriod !== 'daily_custom'
                        "
                    >
                        <label>Frequency *</label>
                        <InputNumber
                            v-model="ruleForm.scheduleFrequency"
                            :min="1"
                            placeholder="Every X"
                            class="w-full"
                            :class="{ 'p-invalid': scheduleFormErrors.frequency }"
                        />
                        <small v-if="scheduleFormErrors.frequency" class="p-error">{{
                            scheduleFormErrors.frequency
                        }}</small>
                        <small class="p-text-secondary">
                            <span v-if="ruleForm.schedulePeriod === 'minute'">Every X minute(s)</span>
                            <span v-else-if="ruleForm.schedulePeriod === 'hourly'">Every X hour(s)</span>
                            <span v-else-if="ruleForm.schedulePeriod === 'daily'">Every X day(s)</span>
                            <span v-else-if="ruleForm.schedulePeriod === 'weekly'">Every X week(s)</span>
                            <span v-else-if="ruleForm.schedulePeriod === 'monthly'">Every X month(s)</span>
                        </small>
                    </div>

                    <div
                        class="field"
                        v-if="
                            ruleForm.schedulePeriod &&
                            ruleForm.schedulePeriod !== 'none' &&
                            (ruleForm.schedulePeriod === 'daily' ||
                                ruleForm.schedulePeriod === 'weekly' ||
                                ruleForm.schedulePeriod === 'monthly')
                        "
                    >
                        <label>Time *</label>
                        <InputText
                            v-model="ruleForm.scheduleTime"
                            placeholder="HH:MM (24-hour format, e.g., 09:00)"
                            class="w-full"
                            :class="{ 'p-invalid': scheduleFormErrors.time }"
                        />
                        <small v-if="scheduleFormErrors.time" class="p-error">{{ scheduleFormErrors.time }}</small>
                        <small class="p-text-secondary"
                            >Time in 24-hour format (e.g., 09:00 for 9 AM, 14:30 for 2:30 PM)</small
                        >
                    </div>

                    <div class="field" v-if="ruleForm.schedulePeriod && ruleForm.schedulePeriod === 'weekly'">
                        <label>Day of Week *</label>
                        <Select
                            v-model="ruleForm.scheduleDayOfWeek"
                            :options="dayOfWeekOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Select day"
                            class="w-full"
                            :class="{ 'p-invalid': scheduleFormErrors.dayOfWeek }"
                        />
                        <small v-if="scheduleFormErrors.dayOfWeek" class="p-error">{{
                            scheduleFormErrors.dayOfWeek
                        }}</small>
                    </div>

                    <div class="field" v-if="ruleForm.schedulePeriod && ruleForm.schedulePeriod === 'monthly'">
                        <label>Day of Month *</label>
                        <InputNumber
                            v-model="ruleForm.scheduleDayOfMonth"
                            :min="1"
                            :max="31"
                            placeholder="1-31"
                            class="w-full"
                            :class="{ 'p-invalid': scheduleFormErrors.dayOfMonth }"
                        />
                        <small v-if="scheduleFormErrors.dayOfMonth" class="p-error">{{
                            scheduleFormErrors.dayOfMonth
                        }}</small>
                    </div>

                    <!-- Custom Daily Schedule: Day/Time Picker -->
                    <div class="field" v-if="ruleForm.schedulePeriod === 'daily_custom'">
                        <label>Select Days and Times *</label>
                        <div class="custom-daily-schedule">
                            <div v-for="day in weekDays" :key="day.value" class="custom-daily-row">
                                <div class="day-checkbox">
                                    <Checkbox
                                        :modelValue="!!ruleForm.customDailySchedule[day.value]"
                                        @update:modelValue="(val) => onDayToggle(day.value, val)"
                                        :inputId="`day-${day.value}`"
                                        :binary="true"
                                    />
                                    <label :for="`day-${day.value}`" class="day-label">{{ day.label }}</label>
                                </div>
                                <InputText
                                    v-model="ruleForm.customDailySchedule[day.value + '_time']"
                                    :disabled="!ruleForm.customDailySchedule[day.value]"
                                    placeholder="HH:MM (e.g., 09:00)"
                                    class="time-input"
                                    :class="{ 'p-invalid': scheduleFormErrors[`day_${day.value}_time`] }"
                                    @blur="validateTime(day.value)"
                                />
                            </div>
                        </div>
                        <small v-if="scheduleFormErrors.customDaily" class="p-error">{{
                            scheduleFormErrors.customDaily
                        }}</small>
                        <small class="p-text-secondary">Select days and set execution times in 24-hour format</small>
                    </div>

                    <div class="field" v-if="ruleForm.schedulePeriod && ruleForm.schedulePeriod !== 'none'">
                        <label>Timezone</label>
                        <Select
                            v-model="ruleForm.scheduleTimezone"
                            :options="timezoneOptions"
                            placeholder="Select timezone"
                            class="w-full"
                        />
                    </div>
                </div>
            </div>

            <!-- Add Scope Dialog -->
            <Dialog
                v-model:visible="showAddScopeDialog"
                header="Add Scope Filter"
                :modal="true"
                :style="{ width: '400px' }"
            >
                <div class="field">
                    <label>Scope Type *</label>
                    <Select
                        v-model="selectedScopeType"
                        :options="availableScopeTypes"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="Select scope type"
                        class="w-full"
                    />
                </div>
                <template #footer>
                    <Button
                        label="Cancel"
                        severity="secondary"
                        @click="
                            showAddScopeDialog = false;
                            selectedScopeType = null;
                        "
                    />
                    <Button label="Add" @click="addScopeFilter" :disabled="!selectedScopeType" />
                </template>
            </Dialog>
            <template #footer>
                <Button label="Cancel" severity="secondary" @click="closeDialog" />
                <Button :label="editingRule ? 'Update' : 'Create'" @click="saveRule" :loading="saving" />
            </template>
        </Dialog>

        <!-- Logs Dialog -->
        <Dialog
            v-model:visible="showLogsDialog"
            header="Rule Execution Logs"
            :modal="true"
            :style="{ maxWidth: '900px', width: '90vw', maxHeight: '90vh' }"
            class="logs-dialog"
        >
            <div v-if="logs.length === 0 && !loadingLogs" class="empty-message">
                <p>No logs available for this rule.</p>
            </div>
            <div v-else class="logs-table-wrapper">
                <DataTable :value="logs" :loading="loadingLogs" paginator :rows="10" :rowsPerPageOptions="[10, 20, 50]">
                    <Column field="status" header="Status" style="width: 100px">
                        <template #body="slotProps">
                            <Tag :value="slotProps.data.status" :severity="getStatusSeverity(slotProps.data.status)" />
                        </template>
                    </Column>
                    <Column
                        field="message"
                        header="Message"
                        style="word-wrap: break-word; overflow-wrap: break-word; white-space: normal; max-width: 300px"
                    >
                        <template #body="slotProps">
                            <span class="message-text">{{ slotProps.data.message }}</span>
                        </template>
                    </Column>
                    <Column field="created_at" header="Time" style="width: 180px">
                        <template #body="slotProps">
                            {{ formatDate(slotProps.data.created_at) }}
                        </template>
                    </Column>
                    <Column header="Actions" style="width: 180px">
                        <template #body="slotProps">
                            <div class="log-actions">
                                <Button
                                    v-if="slotProps.data.details"
                                    icon="pi pi-eye"
                                    severity="secondary"
                                    text
                                    rounded
                                    size="small"
                                    @click="showLogDetails(slotProps.data)"
                                    v-tooltip.top="'View Details'"
                                />
                                <Button
                                    v-if="slotProps.data.details"
                                    icon="pi pi-download"
                                    severity="secondary"
                                    text
                                    rounded
                                    size="small"
                                    @click="downloadLogDetails(slotProps.data)"
                                    v-tooltip.top="'Download Detailed Log'"
                                />
                                <Button
                                    icon="pi pi-trash"
                                    severity="danger"
                                    text
                                    rounded
                                    size="small"
                                    @click="confirmDeleteLog(slotProps.data)"
                                    v-tooltip.top="'Delete Log Entry'"
                                />
                            </div>
                        </template>
                    </Column>
                </DataTable>
            </div>
        </Dialog>

        <!-- Log Details Dialog -->
        <Dialog
            v-model:visible="showLogDetailsDialog"
            header="Log Details"
            :modal="true"
            :style="{ maxWidth: '900px', width: '90vw', maxHeight: '90vh' }"
            class="log-details-dialog"
        >
            <div v-if="selectedLogDetails && selectedLogDetails.details" class="log-details">
                <div v-if="selectedLogDetails.details.decision" class="log-section">
                    <h4>
                        Decision:
                        <Tag
                            :value="selectedLogDetails.details.decision.toUpperCase()"
                            :severity="selectedLogDetails.details.decision === 'proceed' ? 'success' : 'secondary'"
                        />
                    </h4>
                </div>

                <div v-if="selectedLogDetails.details.items_checked !== undefined" class="log-section">
                    <h4>Summary</h4>
                    <p><strong>Items Checked:</strong> {{ selectedLogDetails.details.items_checked }}</p>
                    <p v-if="selectedLogDetails.details.items_meeting_conditions_count !== undefined">
                        <strong>Items Meeting Conditions:</strong>
                        {{ selectedLogDetails.details.items_meeting_conditions_count }}
                    </p>
                </div>

                <div
                    v-if="
                        selectedLogDetails.details.filtered_data && selectedLogDetails.details.filtered_data.length > 0
                    "
                    class="log-section"
                >
                    <h4>Filtered Items ({{ selectedLogDetails.details.filtered_data.length }})</h4>
                    <DataTable :value="selectedLogDetails.details.filtered_data" size="small">
                        <Column field="id" header="ID" />
                        <Column field="name" header="Name" />
                        <Column field="status" header="Status" />
                    </DataTable>
                </div>

                <div
                    v-if="selectedLogDetails.details.evaluations && selectedLogDetails.details.evaluations.length > 0"
                    class="log-section"
                >
                    <h4>Condition Evaluations</h4>
                    <div
                        v-for="(evaluation, idx) in selectedLogDetails.details.evaluations"
                        :key="idx"
                        class="evaluation-item"
                    >
                        <h5>{{ evaluation.item_name }} (ID: {{ evaluation.item_id }})</h5>
                        <div
                            v-for="(cond, condIdx) in evaluation.conditions_evaluated"
                            :key="condIdx"
                            class="condition-result"
                        >
                            <Tag
                                :value="cond.passed ? 'PASS' : 'FAIL'"
                                :severity="cond.passed ? 'success' : 'danger'"
                            />
                            <span class="condition-text">
                                {{ cond.field }} {{ cond.operator }} {{ cond.expected_value }} (actual:
                                {{
                                    cond.actual_value !== null && cond.actual_value !== undefined
                                        ? cond.actual_value
                                        : "N/A"
                                }})
                            </span>
                        </div>
                        <div class="condition-overall">
                            <strong>All Conditions Met:</strong>
                            <Tag
                                :value="evaluation.all_conditions_met ? 'YES' : 'NO'"
                                :severity="evaluation.all_conditions_met ? 'success' : 'danger'"
                            />
                        </div>
                    </div>
                </div>

                <div
                    v-if="
                        selectedLogDetails.details.actions_executed &&
                        selectedLogDetails.details.actions_executed.length > 0
                    "
                    class="log-section"
                >
                    <h4>Actions Executed ({{ selectedLogDetails.details.actions_executed.length }})</h4>
                    <DataTable :value="selectedLogDetails.details.actions_executed" size="small">
                        <Column field="item_name" header="Item Name" />
                        <Column field="item_id" header="Item ID" />
                        <Column field="action_type" header="Action Type">
                            <template #body="slotProps">
                                <Tag
                                    :value="
                                        slotProps.data.action_type === 'set_status' ? 'Set Status' : 'Adjust Budget'
                                    "
                                    :severity="slotProps.data.action_type === 'set_status' ? 'info' : 'warning'"
                                />
                            </template>
                        </Column>
                        <Column field="message" header="Result" />
                        <Column field="success" header="Status">
                            <template #body="slotProps">
                                <Tag
                                    :value="slotProps.data.success ? 'SUCCESS' : 'FAILED'"
                                    :severity="slotProps.data.success ? 'success' : 'danger'"
                                />
                            </template>
                        </Column>
                        <Column
                            v-if="selectedLogDetails.details.actions_executed.some((a) => a.old_budget !== undefined)"
                            field="old_budget"
                            header="Old Budget"
                        >
                            <template #body="slotProps">
                                <span v-if="slotProps.data.old_budget !== undefined"
                                    >${{ slotProps.data.old_budget.toFixed(2) }}</span
                                >
                                <span v-else>-</span>
                            </template>
                        </Column>
                        <Column
                            v-if="selectedLogDetails.details.actions_executed.some((a) => a.new_budget !== undefined)"
                            field="new_budget"
                            header="New Budget"
                        >
                            <template #body="slotProps">
                                <span v-if="slotProps.data.new_budget !== undefined"
                                    >${{ slotProps.data.new_budget.toFixed(2) }}</span
                                >
                                <span v-else>-</span>
                            </template>
                        </Column>
                        <Column
                            v-if="selectedLogDetails.details.actions_executed.some((a) => a.error)"
                            field="error"
                            header="Error"
                        >
                            <template #body="slotProps">
                                <span v-if="slotProps.data.error" class="error-text">{{ slotProps.data.error }}</span>
                                <span v-else>-</span>
                            </template>
                        </Column>
                    </DataTable>
                </div>

                <div v-if="selectedLogDetails.details.error" class="log-section error-section">
                    <h4>Error</h4>
                    <pre>{{ selectedLogDetails.details.error }}</pre>
                </div>

                <div
                    v-if="
                        selectedLogDetails.details.rule_level ||
                        selectedLogDetails.details.scope_filters ||
                        selectedLogDetails.details.time_range
                    "
                    class="log-section"
                >
                    <h4>Rule Configuration</h4>
                    <p v-if="selectedLogDetails.details.rule_level">
                        <strong>Rule Level:</strong> {{ selectedLogDetails.details.rule_level }}
                    </p>
                    <p v-if="selectedLogDetails.details.scope_filters">
                        <strong>Scope Filters:</strong>
                        {{ JSON.stringify(selectedLogDetails.details.scope_filters, null, 2) }}
                    </p>
                    <p v-if="selectedLogDetails.details.time_range">
                        <strong>Time Range:</strong>
                        {{ JSON.stringify(selectedLogDetails.details.time_range, null, 2) }}
                    </p>
                </div>

                <div v-if="selectedLogDetails.details.data_fetch" class="log-section">
                    <h4>Data Fetch Summary</h4>
                    <p>
                        <strong>Total Items Fetched:</strong>
                        {{ selectedLogDetails.details.data_fetch.total_items || 0 }}
                    </p>
                </div>
            </div>
            <div v-else class="empty-message">
                <p>No detailed information available for this log entry.</p>
            </div>
            <template #footer>
                <Button label="Close" severity="secondary" @click="showLogDetailsDialog = false" />
            </template>
        </Dialog>

        <Toast />
        <ConfirmDialog />
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Button from "primevue/button";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import InputNumber from "primevue/inputnumber";
import Textarea from "primevue/textarea";
import Password from "primevue/password";
import Checkbox from "primevue/checkbox";
import InputSwitch from "primevue/inputswitch";
import Select from "primevue/select";
import Tag from "primevue/tag";
import Toast from "primevue/toast";
import ConfirmDialog from "primevue/confirmdialog";
import Chips from "primevue/chips";
import {
    getRules,
    createRule,
    updateRule,
    deleteRule,
    getRuleLogs,
    testRule as testRuleApi,
    deleteRuleLog,
} from "@/api/metaCampaignsApi";
import {
    getAdAccounts,
    getDefaultAdAccount,
    createAdAccount,
    updateAdAccount,
    deleteAdAccount,
    getAdAccountCampaigns,
    getCampaignAdSets,
    getAdSetAds,
    testAdAccountConnection,
} from "@/api/adAccountsApi";

const toast = useToast();
const confirm = useConfirm();

const adAccounts = ref([]);
const selectedAccount = ref(null);
const campaigns = ref([]);
const adSets = ref([]);
const ads = ref([]);
const campaignsView = ref('campaigns'); // 'campaigns', 'adsets', 'ads'
const selectedCampaign = ref(null);
const selectedAdSet = ref(null);
const rules = ref([]);
const logs = ref([]);
const loadingAccounts = ref(false);
const loadingCampaigns = ref(false);
const loadingAdSets = ref(false);
const loadingAds = ref(false);
const loading = ref(false);
const loadingLogs = ref(false);
const savingAccount = ref(false);
const saving = ref(false);
const testingRuleId = ref(null);
const testingConnection = ref(false);
const showAdAccountDialog = ref(false);
const showCreateDialog = ref(false);
const showLogsDialog = ref(false);
const showLogDetailsDialog = ref(false);
const showCampaigns = ref(false);
const editingAccount = ref(null);
const editingRule = ref(null);
const selectedLogDetails = ref(null);
const connectionStatus = ref(null);
const connectionLastChecked = ref(null);

const accountForm = ref({
    name: "",
    description: "",
    meta_account_id: "",
    meta_access_token: "",
    slack_webhook_url: "",
    is_default: false,
});

const ruleForm = ref({
    name: "",
    description: "",
    schedule_cron: "",
    enabled: true,
    // Section 2: Level and Scope
    ruleLevel: null, // 'ad', 'ad_set', or 'campaign'
    scopeFilters: [], // Array of { type, value }
    // Section 3: Time Range
    timeRangeUnit: null, // 'minutes', 'hours', 'days'
    timeRangeAmount: null,
    excludeToday: true,
    // Section 4: Conditions (array for UI)
    conditions: [], // Array of { field, operator, value }
    // Section 5: Actions (array for UI)
    actions: [], // Array of action objects
    // Section 6: Scheduling fields
    schedulePeriod: null,
    scheduleFrequency: 1,
    scheduleTime: null,
    scheduleDayOfWeek: null,
    scheduleDayOfMonth: null,
    scheduleTimezone: "UTC",
    // Custom daily schedule: { "0": "09:00", "1": "14:30", ... } where key is day (0=Sunday, 1=Monday, etc.)
    customDailySchedule: {},
});

const scheduleFormErrors = ref({});
const formErrors = ref({});
const showAddScopeDialog = ref(false);
const selectedScopeType = ref(null);

const periodOptions = [
    { label: "None", value: "none" },
    { label: "Minute", value: "minute" },
    { label: "Hourly", value: "hourly" },
    { label: "Daily", value: "daily" },
    { label: "Daily at Custom Times", value: "daily_custom" },
    { label: "Weekly", value: "weekly" },
    { label: "Monthly", value: "monthly" },
];

const dayOfWeekOptions = [
    { label: "Monday", value: 1 },
    { label: "Tuesday", value: 2 },
    { label: "Wednesday", value: 3 },
    { label: "Thursday", value: 4 },
    { label: "Friday", value: 5 },
    { label: "Saturday", value: 6 },
    { label: "Sunday", value: 0 },
];

const weekDays = [
    { label: "Sunday", value: 0 },
    { label: "Monday", value: 1 },
    { label: "Tuesday", value: 2 },
    { label: "Wednesday", value: 3 },
    { label: "Thursday", value: 4 },
    { label: "Friday", value: 5 },
    { label: "Saturday", value: 6 },
];

const timezoneOptions = [
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Paris",
    "Asia/Jerusalem",
    "Asia/Tokyo",
    "Australia/Sydney",
];

// Section 2: Rule Level options
const ruleLevelOptions = [
    { label: "Ad", value: "ad" },
    { label: "Ad Set", value: "ad_set" },
    { label: "Campaign", value: "campaign" },
];

// Scope type options
const scopeTypeOptions = [
    { label: "Name contains", value: "name_contains" },
    { label: "IDs", value: "ids" },
    { label: "Campaign Name contains", value: "campaign_name_contains" },
    { label: "Campaign IDs", value: "campaign_ids" },
];

// Section 3: Time Range Unit options
const timeRangeUnitOptions = [
    { label: "Minutes", value: "minutes" },
    { label: "Hours", value: "hours" },
    { label: "Days", value: "days" },
];

// Section 4: Operator options
const operatorOptions = [
    { label: ">", value: ">" },
    { label: ">=", value: ">=" },
    { label: "<", value: "<" },
    { label: "<=", value: "<=" },
    { label: "=", value: "=" },
    { label: "!=", value: "!=" },
];

// Condition fields for Ad level
const adConditionFields = [
    { label: "Cost Per Purchase", value: "cpp" },
    { label: "Spend", value: "spend" },
    { label: "Conversions", value: "conversions" },
    { label: "CTR", value: "ctr" },
    { label: "CPC", value: "cpc" },
    { label: "CPM", value: "cpm" },
    { label: "Status", value: "status" },
    { label: "Campaign Status", value: "campaign_status" },
];

// Condition fields for Ad Set level
const adSetConditionFields = [
    { label: "Cost Per Purchase", value: "cpp" },
    { label: "Spend", value: "spend" },
    { label: "Conversions", value: "conversions" },
    { label: "ROAS", value: "roas" },
    { label: "Daily budget", value: "daily_budget" },
    { label: "Status", value: "status" },
    { label: "Campaign Status", value: "campaign_status" },
];

// Condition fields for Campaign level
const campaignConditionFields = [
    { label: "Cost Per Purchase", value: "cpp" },
    { label: "Spend", value: "spend" },
    { label: "Conversions", value: "conversions" },
    { label: "ROAS", value: "roas" },
    { label: "Status", value: "status" },
];

// Status options
const statusOptions = [
    { label: "ACTIVE", value: "ACTIVE" },
    { label: "PAUSED", value: "PAUSED" },
    { label: "DELETED", value: "DELETED" },
];

// Budget direction options
const budgetDirectionOptions = [
    { label: "Increase", value: "increase" },
    { label: "Decrease", value: "decrease" },
];

// Computed: Available scope types (excluding already added ones)
const availableScopeTypes = computed(() => {
    const addedTypes = ruleForm.value.scopeFilters.map((s) => s.type);
    // Filter out campaign-level scope filters when rule level is campaign (redundant)
    let filteredOptions = scopeTypeOptions;
    if (ruleForm.value.ruleLevel === "campaign") {
        filteredOptions = scopeTypeOptions.filter(
            (opt) => opt.value !== "campaign_name_contains" && opt.value !== "campaign_ids"
        );
    }
    return filteredOptions.filter((opt) => !addedTypes.includes(opt.value));
});

// Computed: Available condition fields based on rule level
const availableConditionFields = computed(() => {
    if (ruleForm.value.ruleLevel === "ad") {
        return adConditionFields;
    } else if (ruleForm.value.ruleLevel === "ad_set") {
        return adSetConditionFields;
    } else if (ruleForm.value.ruleLevel === "campaign") {
        return campaignConditionFields;
    }
    return [];
});

// Computed: Available action types based on rule level
const availableActionTypes = computed(() => {
    if (ruleForm.value.ruleLevel === "ad") {
        return [
            { label: "Set Status", value: "set_status" },
            { label: "Send Notification", value: "send_notification" },
        ];
    } else if (ruleForm.value.ruleLevel === "ad_set") {
        return [
            { label: "Adjust Daily Budget by Percentage", value: "adjust_daily_budget" },
            { label: "Set Status", value: "set_status" },
            { label: "Send Notification", value: "send_notification" },
        ];
    } else if (ruleForm.value.ruleLevel === "campaign") {
        return [
            { label: "Set Status", value: "set_status" },
            { label: "Send Notification", value: "send_notification" },
        ];
    }
    return [];
});

let rulesPollingInterval = null;

onMounted(async () => {
    await loadAdAccounts();
    // Select default account if available
    try {
        const defaultAccount = await getDefaultAdAccount();
        selectedAccount.value = defaultAccount;
        await loadRules();
    } catch (error) {
        // No default account yet
    }

    // Start polling for rules updates every 5 seconds (silent refresh)
    rulesPollingInterval = setInterval(() => {
        if (selectedAccount.value) {
            loadRules(true); // silent = true to avoid loading indicator flicker
        }
    }, 5000);
});

onUnmounted(() => {
    // Clear polling interval when component is unmounted
    if (rulesPollingInterval) {
        clearInterval(rulesPollingInterval);
        rulesPollingInterval = null;
    }
});

watch(selectedAccount, async (newAccount) => {
    if (newAccount) {
        await loadRules();
    } else {
        rules.value = [];
    }
});

async function loadAdAccounts() {
    loadingAccounts.value = true;
    try {
        adAccounts.value = await getAdAccounts();
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: "Failed to load ad accounts",
            life: 5000,
        });
    } finally {
        loadingAccounts.value = false;
    }
}

async function loadRules(silent = false) {
    if (!selectedAccount.value) return;

    if (!silent) {
        loading.value = true;
    }
    try {
        rules.value = await getRules(selectedAccount.value.id);
    } catch (error) {
        // Only show error toast if not silent (manual refresh)
        if (!silent) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: "Failed to load rules",
                life: 5000,
            });
        }
    } finally {
        if (!silent) {
            loading.value = false;
        }
    }
}

function onAccountSelect(event) {
    selectedAccount.value = event.data;
    // Clear campaigns and hide section when account changes
    campaigns.value = [];
    adSets.value = [];
    ads.value = [];
    campaignsView.value = 'campaigns';
    selectedCampaign.value = null;
    selectedAdSet.value = null;
    showCampaigns.value = false;
}

async function loadCampaigns() {
    if (!selectedAccount.value) {
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
        const response = await getAdAccountCampaigns(selectedAccount.value.id);
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

function getCampaignStatusSeverity(status) {
    if (!status) return "secondary";
    const upperStatus = status.toUpperCase();
    if (upperStatus === "ACTIVE") return "success";
    if (upperStatus === "PAUSED") return "warning";
    if (upperStatus === "DELETED" || upperStatus === "ARCHIVED") return "danger";
    return "secondary";
}

function getViewTitle() {
    if (campaignsView.value === 'adsets') {
        return {
            prefix: 'Ad Sets for',
            name: selectedCampaign.value?.name || 'Campaign'
        };
    } else if (campaignsView.value === 'ads') {
        return {
            prefix: 'Ads for',
            name: selectedAdSet.value?.name || 'Ad Set'
        };
    }
    return {
        prefix: 'Campaigns for',
        name: selectedAccount.value?.name || ''
    };
}

function onCampaignClick(event) {
    const campaign = event.data;
    selectedCampaign.value = campaign;
    campaignsView.value = 'adsets';
    loadAdSets(campaign.id);
}

function onAdSetClick(event) {
    const adSet = event.data;
    selectedAdSet.value = adSet;
    campaignsView.value = 'ads';
    loadAds(adSet.id);
}

async function loadAdSets(campaignId) {
    if (!selectedAccount.value) return;

    loadingAdSets.value = true;
    try {
        const response = await getCampaignAdSets(selectedAccount.value.id, campaignId);
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

async function loadAds(adsetId) {
    if (!selectedAccount.value) return;

    loadingAds.value = true;
    try {
        const response = await getAdSetAds(selectedAccount.value.id, adsetId);
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
    if (campaignsView.value === 'ads') {
        // Go back to ad sets
        campaignsView.value = 'adsets';
        ads.value = [];
        selectedAdSet.value = null;
    } else if (campaignsView.value === 'adsets') {
        // Go back to campaigns
        campaignsView.value = 'campaigns';
        adSets.value = [];
        selectedCampaign.value = null;
    }
}

function editAdAccount(account) {
    editingAccount.value = account;
    accountForm.value = {
        name: account.name,
        description: account.description || "",
        meta_account_id: account.meta_account_id || "",
        meta_access_token: account.meta_access_token || "",
        slack_webhook_url: account.slack_webhook_url || "",
        is_default: account.is_default || false,
    };
    // Load connection status
    connectionStatus.value = account.connection_status ?? null;
    connectionLastChecked.value = account.connection_last_checked ? new Date(account.connection_last_checked) : null;
    showAdAccountDialog.value = true;
}

function openCreateAdAccountDialog() {
    // Reset form and clear editing state
    editingAccount.value = null;
    connectionStatus.value = null;
    connectionLastChecked.value = null;
    accountForm.value = {
        name: "",
        description: "",
        meta_account_id: "",
        meta_access_token: "",
        slack_webhook_url: "",
        is_default: false,
    };
    showAdAccountDialog.value = true;
}

function closeAccountDialog() {
    showAdAccountDialog.value = false;
    editingAccount.value = null;
    connectionStatus.value = null;
    connectionLastChecked.value = null;
    accountForm.value = {
        name: "",
        description: "",
        meta_account_id: "",
        meta_access_token: "",
        slack_webhook_url: "",
        is_default: false,
    };
}

async function testConnection() {
    if (!editingAccount.value) return;

    testingConnection.value = true;
    try {
        const result = await testAdAccountConnection(editingAccount.value.id);

        // Update connection status
        connectionStatus.value = result.connection_status;
        connectionLastChecked.value = result.connection_last_checked ? new Date(result.connection_last_checked) : null;

        // Show toast based on result
        if (result.success) {
            toast.add({
                severity: "success",
                summary: "Connection Test",
                detail: result.message,
                life: 3000,
            });
        } else {
            if (result.cooldown_active) {
                toast.add({
                    severity: "warn",
                    summary: "Cooldown Active",
                    detail: result.message,
                    life: 3000,
                });
            } else {
                toast.add({
                    severity: "error",
                    summary: "Connection Test Failed",
                    detail: result.message,
                    life: 5000,
                });
            }
        }

        // Refresh account data to get updated status
        await loadAdAccounts();
        const updatedAccount = adAccounts.value.find(a => a.id === editingAccount.value.id);
        if (updatedAccount) {
            editingAccount.value = updatedAccount;
        }
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: error.message || "Failed to test connection",
            life: 5000,
        });
    } finally {
        testingConnection.value = false;
    }
}

function formatDate(date) {
    if (!date) return "";
    const d = new Date(date);
    return d.toLocaleString();
}

async function saveAdAccount() {
    savingAccount.value = true;
    try {
        if (editingAccount.value) {
            await updateAdAccount(editingAccount.value.id, accountForm.value);
            toast.add({
                severity: "success",
                summary: "Success",
                detail: "Ad account updated successfully",
                life: 3000,
            });
        } else {
            await createAdAccount(accountForm.value);
            toast.add({
                severity: "success",
                summary: "Success",
                detail: "Ad account created successfully",
                life: 3000,
            });
        }
        closeAccountDialog();
        await loadAdAccounts();
        // If default was set, select it
        if (accountForm.value.is_default) {
            const accounts = await getAdAccounts();
            const defaultAcc = accounts.find((a) => a.is_default);
            if (defaultAcc) {
                selectedAccount.value = defaultAcc;
            }
        }
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: error.message || "Failed to save ad account",
            life: 5000,
        });
    } finally {
        savingAccount.value = false;
    }
}

function confirmDeleteAccount(account) {
    confirm.require({
        message: `Are you sure you want to delete "${account.name}"? This will also delete all associated rules.`,
        header: "Confirm Delete",
        icon: "pi pi-exclamation-triangle",
        accept: async () => {
            try {
                await deleteAdAccount(account.id);
                toast.add({
                    severity: "success",
                    summary: "Success",
                    detail: "Ad account deleted successfully",
                    life: 3000,
                });
                if (selectedAccount.value?.id === account.id) {
                    selectedAccount.value = null;
                }
                await loadAdAccounts();
            } catch (error) {
                toast.add({
                    severity: "error",
                    summary: "Error",
                    detail: "Failed to delete ad account",
                    life: 5000,
                });
            }
        },
    });
}

// Helper functions for scope filters
function getScopeTypeLabel(type) {
    const option = scopeTypeOptions.find((opt) => opt.value === type);
    let label = option ? option.label : type;
    // Make IDs label dynamic based on rule level
    if (type === "ids") {
        if (ruleForm.value.ruleLevel === "ad") {
            label = "Ad ID";
        } else if (ruleForm.value.ruleLevel === "ad_set") {
            label = "Ad Set ID";
        }
    }
    return label;
}

function addScopeFilter() {
    if (!selectedScopeType.value) return;

    const newScope = {
        type: selectedScopeType.value,
        value: selectedScopeType.value === "name_contains" ? [] : "",
    };

    ruleForm.value.scopeFilters.push(newScope);
    showAddScopeDialog.value = false;
    selectedScopeType.value = null;
}

function removeScopeFilter(index) {
    ruleForm.value.scopeFilters.splice(index, 1);
}

// Helper functions for conditions
function isNumericField(field) {
    const numericFields = ["cpp", "spend", "conversions", "ctr", "cpc", "cpm", "roas", "daily_budget"];
    return numericFields.includes(field);
}

function getValuePlaceholder(field) {
    if (field === "status" || field === "campaign_status") {
        return "ACTIVE or PAUSED";
    } else if (field === "name_contains") {
        return "Enter text to match";
    }
    return "Enter value";
}

function addCondition() {
    ruleForm.value.conditions.push({
        field: null,
        operator: null,
        value: null,
    });
}

function removeCondition(index) {
    ruleForm.value.conditions.splice(index, 1);
}

function onConditionFieldChange(index) {
    // Reset value when field changes
    ruleForm.value.conditions[index].value = null;
}

// Helper functions for actions
function addAction() {
    ruleForm.value.actions.push({
        type: null,
        status: null,
        direction: null,
        percent: null,
        minCap: null,
        maxCap: null,
        sendSlackNotification: true, // Default to true for all actions
    });
}

function removeAction(index) {
    ruleForm.value.actions.splice(index, 1);
}

function onActionTypeChange(index) {
    // Reset action-specific fields when type changes
    const action = ruleForm.value.actions[index];
    action.status = null;
    action.direction = null;
    action.percent = null;
    action.minCap = null;
    action.maxCap = null;
    // For send_notification, always enable slack notification
    if (action.type === "send_notification") {
        action.sendSlackNotification = true;
    } else {
        // Preserve sendSlackNotification if it exists, otherwise set to true
        if (action.sendSlackNotification === undefined) {
            action.sendSlackNotification = true;
        }
    }
}

function onRuleLevelChange() {
    // Clear conditions and actions when rule level changes
    ruleForm.value.conditions = [];
    ruleForm.value.actions = [];
}

// Helper to parse IDs from textarea (comma or newline separated) or return array as-is
function parseIds(text) {
    // If it's already an array (from Chips component), return it filtered
    if (Array.isArray(text)) {
        return text.filter((id) => id && String(id).trim().length > 0);
    }
    // If it's a string, parse it
    if (typeof text === "string") {
        if (!text || !text.trim()) return [];
        return text
            .split(/[,\n]/)
            .map((id) => id.trim())
            .filter((id) => id.length > 0);
    }
    // If it's something else, return empty array
    return [];
}

// Helper to format IDs to textarea text
function formatIds(ids) {
    if (!ids || !Array.isArray(ids)) return "";
    return ids.join("\n");
}

function editRule(rule) {
    editingRule.value = rule;
    // Try to parse existing cron expression
    const parsed = parseCronExpression(rule.schedule_cron);

    const conditions = rule.conditions || {};
    const actions = rule.actions || {};

    // Parse scope filters
    const scopeFilters = [];

    if (conditions.name_contains) {
        if (Array.isArray(conditions.name_contains) && conditions.name_contains.length > 0) {
            scopeFilters.push({ type: "name_contains", value: conditions.name_contains });
        } else if (typeof conditions.name_contains === "string" && conditions.name_contains.trim().length > 0) {
            // Handle case where it might be stored as a single string
            scopeFilters.push({ type: "name_contains", value: [conditions.name_contains.trim()] });
        }
    }
    if (conditions.ids) {
        if (Array.isArray(conditions.ids) && conditions.ids.length > 0) {
            scopeFilters.push({ type: "ids", value: conditions.ids });
        } else if (typeof conditions.ids === "string" && conditions.ids.trim().length > 0) {
            // Handle legacy format (comma-separated string) - convert to array
            const ids = parseIds(conditions.ids);
            if (ids.length > 0) {
                scopeFilters.push({ type: "ids", value: ids });
            }
        }
    }
    if (conditions.campaign_name_contains) {
        if (Array.isArray(conditions.campaign_name_contains) && conditions.campaign_name_contains.length > 0) {
            scopeFilters.push({ type: "campaign_name_contains", value: conditions.campaign_name_contains });
        } else if (
            typeof conditions.campaign_name_contains === "string" &&
            conditions.campaign_name_contains.trim().length > 0
        ) {
            scopeFilters.push({ type: "campaign_name_contains", value: [conditions.campaign_name_contains.trim()] });
        }
    }
    if (conditions.campaign_ids) {
        if (Array.isArray(conditions.campaign_ids) && conditions.campaign_ids.length > 0) {
            scopeFilters.push({ type: "campaign_ids", value: conditions.campaign_ids });
        } else if (typeof conditions.campaign_ids === "string" && conditions.campaign_ids.trim().length > 0) {
            // Handle legacy format (comma-separated string) - convert to array
            const ids = parseIds(conditions.campaign_ids);
            if (ids.length > 0) {
                scopeFilters.push({ type: "campaign_ids", value: ids });
            }
        }
    }


    // Parse conditions array
    const conditionsArray = conditions.conditions || [];

    // Parse actions array and ensure sendSlackNotification is set
    const actionsArray = (actions.actions || []).map((action) => {
        const actionObj = {
            type: action.type,
            status: action.status || null,
            direction: action.direction || null,
            percent: action.percent || null,
            minCap: action.min_cap || null,
            maxCap: action.max_cap || null,
            // For send_notification, always set to true; otherwise use the value from backend or default to true
            sendSlackNotification:
                action.type === "send_notification"
                    ? true
                    : action.send_slack_notification !== undefined
                    ? action.send_slack_notification
                    : true,
        };
        return actionObj;
    });

    // Parse time range
    const timeRange = conditions.time_range || {};

    ruleForm.value = {
        name: rule.name,
        description: rule.description || "",
        schedule_cron: rule.schedule_cron,
        enabled: rule.enabled,
        // Section 2
        ruleLevel: conditions.rule_level || null,
        scopeFilters: scopeFilters,
        // Section 3
        timeRangeUnit: timeRange.unit || null,
        timeRangeAmount: timeRange.amount || null,
        excludeToday: timeRange.exclude_today !== undefined ? timeRange.exclude_today : true,
        // Section 4 (UI array)
        conditions: conditionsArray,
        // Section 5 (UI array)
        actions: actionsArray,
        // Section 6
        schedulePeriod: parsed.period || "none",
        scheduleFrequency: parsed.frequency || 1,
        scheduleTime: parsed.time || null,
        scheduleDayOfWeek: parsed.dayOfWeek !== null ? parsed.dayOfWeek : null,
        scheduleDayOfMonth: parsed.dayOfMonth !== null && parsed.dayOfMonth !== undefined ? parsed.dayOfMonth : null,
        scheduleTimezone: parsed.timezone || "UTC",
        customDailySchedule: parsed.customDailySchedule || {},
    };


    scheduleFormErrors.value = {};
    formErrors.value = {};
    showCreateDialog.value = true;
}

function closeDialog() {
    showCreateDialog.value = false;
    editingRule.value = null;
    ruleForm.value = {
        name: "",
        description: "",
        schedule_cron: "",
        enabled: true,
        ruleLevel: null,
        scopeFilters: [],
        timeRangeUnit: null,
        timeRangeAmount: null,
        excludeToday: true,
        conditions: [],
        actions: [],
        schedulePeriod: null,
        scheduleFrequency: 1,
        scheduleTime: null,
        scheduleDayOfWeek: null,
        scheduleDayOfMonth: null,
        scheduleTimezone: "UTC",
        customDailySchedule: {},
    };
    scheduleFormErrors.value = {};
    formErrors.value = {};
    showAddScopeDialog.value = false;
    selectedScopeType.value = null;
}

function openCreateDialog() {
    // Reset form to ensure clean state when opening create dialog
    editingRule.value = null;
    ruleForm.value = {
        name: "",
        description: "",
        schedule_cron: "",
        enabled: true,
        ruleLevel: null,
        scopeFilters: [],
        timeRangeUnit: null,
        timeRangeAmount: null,
        excludeToday: true,
        conditions: [],
        actions: [],
        schedulePeriod: null,
        scheduleFrequency: 1,
        scheduleTime: null,
        scheduleDayOfWeek: null,
        scheduleDayOfMonth: null,
        scheduleTimezone: "UTC",
        customDailySchedule: {},
    };
    scheduleFormErrors.value = {};
    formErrors.value = {};
    showAddScopeDialog.value = false;
    selectedScopeType.value = null;
    showCreateDialog.value = true;
}

function onSchedulePeriodChange() {
    // Reset dependent fields when period changes
    ruleForm.value.scheduleDayOfWeek = null;
    ruleForm.value.scheduleDayOfMonth = null;
    scheduleFormErrors.value = {};

    // Reset custom daily schedule if switching away from it
    if (ruleForm.value.schedulePeriod !== "daily_custom") {
        ruleForm.value.customDailySchedule = {};
    } else if (ruleForm.value.schedulePeriod === "daily_custom") {
        // Initialize custom daily schedule if empty
        if (!ruleForm.value.customDailySchedule || Object.keys(ruleForm.value.customDailySchedule).length === 0) {
            ruleForm.value.customDailySchedule = {};
        }
    }
}

function onDayToggle(dayValue, checked) {
    if (!ruleForm.value.customDailySchedule) {
        ruleForm.value.customDailySchedule = {};
    }
    if (checked) {
        ruleForm.value.customDailySchedule[dayValue] = true;
        // Set default time if not set
        if (!ruleForm.value.customDailySchedule[dayValue + "_time"]) {
            ruleForm.value.customDailySchedule[dayValue + "_time"] = "12:00";
        }
    } else {
        ruleForm.value.customDailySchedule[dayValue] = false;
        // Clear time when unchecked
        delete ruleForm.value.customDailySchedule[dayValue + "_time"];
    }
}

function validateTime(dayValue) {
    const timeKey = dayValue + "_time";
    const time = ruleForm.value.customDailySchedule[timeKey];
    if (time) {
        const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
        if (!timeRegex.test(time)) {
            scheduleFormErrors.value[`day_${dayValue}_time`] = "Time must be in HH:MM format (24-hour)";
        } else {
            delete scheduleFormErrors.value[`day_${dayValue}_time`];
        }
    }
}

function validateSchedule() {
    scheduleFormErrors.value = {};

    // If period is 'none' or null/empty, no validation needed
    if (!ruleForm.value.schedulePeriod || ruleForm.value.schedulePeriod === "none") {
        return true;
    }

    if (!ruleForm.value.scheduleFrequency || ruleForm.value.scheduleFrequency < 1) {
        scheduleFormErrors.value.frequency = "Frequency must be at least 1";
    }

    if (ruleForm.value.schedulePeriod === "minute" || ruleForm.value.schedulePeriod === "hourly") {
        // Minute and hourly don't need time, day_of_week, or day_of_month
    } else if (ruleForm.value.schedulePeriod === "daily") {
        if (!ruleForm.value.scheduleTime) {
            scheduleFormErrors.value.time = "Time is required for daily period";
        } else {
            const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
            if (!timeRegex.test(ruleForm.value.scheduleTime)) {
                scheduleFormErrors.value.time = "Time must be in HH:MM format (24-hour)";
            }
        }
    } else if (ruleForm.value.schedulePeriod === "weekly") {
        if (!ruleForm.value.scheduleTime) {
            scheduleFormErrors.value.time = "Time is required for weekly period";
        } else {
            const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
            if (!timeRegex.test(ruleForm.value.scheduleTime)) {
                scheduleFormErrors.value.time = "Time must be in HH:MM format (24-hour)";
            }
        }
        if (ruleForm.value.scheduleDayOfWeek === null) {
            scheduleFormErrors.value.dayOfWeek = "Day of week is required for weekly period";
        }
    } else if (ruleForm.value.schedulePeriod === "monthly") {
        if (!ruleForm.value.scheduleTime) {
            scheduleFormErrors.value.time = "Time is required for monthly period";
        } else {
            const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
            if (!timeRegex.test(ruleForm.value.scheduleTime)) {
                scheduleFormErrors.value.time = "Time must be in HH:MM format (24-hour)";
            }
        }
        if (ruleForm.value.scheduleDayOfMonth === null) {
            scheduleFormErrors.value.dayOfMonth = "Day of month is required for monthly period";
        } else if (ruleForm.value.scheduleDayOfMonth < 1 || ruleForm.value.scheduleDayOfMonth > 31) {
            scheduleFormErrors.value.dayOfMonth = "Day of month must be between 1 and 31";
        }
    } else if (ruleForm.value.schedulePeriod === "daily_custom") {
        // Validate custom daily schedule
        const selectedDays = weekDays.filter((day) => ruleForm.value.customDailySchedule[day.value]);
        if (selectedDays.length === 0) {
            scheduleFormErrors.value.customDaily = "At least one day must be selected";
        } else {
            delete scheduleFormErrors.value.customDaily;
            // Validate times for selected days
            let hasInvalidTime = false;
            selectedDays.forEach((day) => {
                const timeKey = day.value + "_time";
                const time = ruleForm.value.customDailySchedule[timeKey];
                if (!time) {
                    scheduleFormErrors.value[`day_${day.value}_time`] = "Time is required for selected day";
                    hasInvalidTime = true;
                } else {
                    const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
                    if (!timeRegex.test(time)) {
                        scheduleFormErrors.value[`day_${day.value}_time`] = "Time must be in HH:MM format (24-hour)";
                        hasInvalidTime = true;
                    } else {
                        delete scheduleFormErrors.value[`day_${day.value}_time`];
                    }
                }
            });
            if (!hasInvalidTime) {
                delete scheduleFormErrors.value.customDaily;
            }
        }
    }

    return Object.keys(scheduleFormErrors.value).length === 0;
}

function buildCronExpression() {
    const {
        schedulePeriod,
        scheduleFrequency,
        scheduleTime,
        scheduleDayOfWeek,
        scheduleDayOfMonth,
        customDailySchedule,
    } = ruleForm.value;

    if (!schedulePeriod || schedulePeriod === "none") {
        return null;
    }

    // Handle custom daily schedule - store as JSON string
    if (schedulePeriod === "daily_custom") {
        const schedule = {};
        weekDays.forEach((day) => {
            if (customDailySchedule[day.value]) {
                const time = customDailySchedule[day.value + "_time"];
                if (time) {
                    schedule[day.value] = time;
                }
            }
        });
        // Store as JSON string with prefix to identify it, including timezone
        return JSON.stringify({
            type: "custom_daily",
            schedule: schedule,
            timezone: ruleForm.value.scheduleTimezone || "UTC",
        });
    }

    let cron = "";

    if (schedulePeriod === "minute") {
        // Every X minutes: */X * * * *
        cron = `*/${scheduleFrequency} * * * *`;
    } else if (schedulePeriod === "hourly") {
        // Every X hours: 0 */X * * *
        cron = `0 */${scheduleFrequency} * * *`;
    } else if (schedulePeriod === "daily") {
        // Daily at specific time: minute hour * * *
        // Note: Cron doesn't support "every X days" directly, so frequency is only used for UI
        // For frequency > 1, this would require tracking last run date which is beyond simple cron
        const [hour, minute] = scheduleTime ? scheduleTime.split(":") : ["0", "0"];
        if (scheduleFrequency === 1) {
            cron = `${minute || 0} ${hour || 0} * * *`;
        } else {
            // For frequency > 1, we approximate with day of month pattern
            // This is a simplified approach - for true "every X days", you'd need job queue tracking
            cron = `${minute || 0} ${hour || 0} */${scheduleFrequency} * *`;
        }
    } else if (schedulePeriod === "weekly") {
        // Weekly on specific day at specific time: minute hour * * dayOfWeek
        // Note: Cron doesn't support "every X weeks" directly
        const [hour, minute] = scheduleTime ? scheduleTime.split(":") : ["0", "0"];
        // Cron uses 0-6 for Sunday-Saturday, our format uses 0 for Sunday, 1-6 for Mon-Sat
        const cronDayOfWeek = scheduleDayOfWeek !== null && scheduleDayOfWeek !== undefined ? scheduleDayOfWeek : "*";
        cron = `${minute || 0} ${hour || 0} * * ${cronDayOfWeek}`;
    } else if (schedulePeriod === "monthly") {
        // Monthly on specific day at specific time: minute hour dayOfMonth * *
        // For frequency > 1 (every X months), we use: minute hour dayOfMonth */X *
        const [hour, minute] = scheduleTime ? scheduleTime.split(":") : ["0", "0"];
        const day = scheduleDayOfMonth || 1;
        if (scheduleFrequency === 1) {
            cron = `${minute || 0} ${hour || 0} ${day} * *`;
        } else {
            cron = `${minute || 0} ${hour || 0} ${day} */${scheduleFrequency} *`;
        }
    }

    // Wrap all schedule types in JSON to include timezone (ensures timezone is always preserved)
    const timezone = ruleForm.value.scheduleTimezone || "UTC";
    // Always use JSON format to ensure timezone is preserved for all schedule types
    return JSON.stringify({
        type: schedulePeriod,
        cron: cron,
        timezone: timezone,
    });
}

function parseCronExpression(cron) {
    if (!cron) {
        return {
            period: "none",
            frequency: 1,
            time: null,
            dayOfWeek: null,
            dayOfMonth: null,
            timezone: "UTC",
            customDailySchedule: {},
        };
    }

    // Check if it's a JSON-wrapped schedule (all schedule types now support timezone)
    try {
        const parsed = JSON.parse(cron);

        // Handle custom daily schedule
        if (parsed.type === "custom_daily" && parsed.schedule) {
            const customSchedule = {};
            Object.keys(parsed.schedule).forEach((dayValue) => {
                customSchedule[dayValue] = true;
                customSchedule[dayValue + "_time"] = parsed.schedule[dayValue];
            });
            return {
                period: "daily_custom",
                frequency: 1,
                time: null,
                dayOfWeek: null,
                dayOfMonth: null,
                timezone: parsed.timezone || "UTC",
                customDailySchedule: customSchedule,
            };
        }

        // Handle other schedule types wrapped in JSON (with timezone support)
        if (parsed.type && parsed.cron) {
            // Parse the cron expression to extract schedule details (parse only the cron part, not recursively)
            const cronParsed = parseCronStringOnly(parsed.cron);
            // Override timezone from JSON wrapper
            cronParsed.timezone = parsed.timezone || "UTC";
            return cronParsed;
        }
    } catch (e) {
        // Not JSON, continue with legacy cron parsing (defaults to UTC)
    }

    // If we get here, it's a legacy plain cron string - parse it
    return parseCronStringOnly(cron);
}

function parseCronStringOnly(cron) {
    // Helper function to parse just the cron string part (not JSON-wrapped)
    const parts = cron.split(/\s+/);
    if (parts.length !== 5) {
        return {
            period: null,
            frequency: 1,
            time: null,
            dayOfWeek: null,
            dayOfMonth: null,
            timezone: "UTC",
            customDailySchedule: {},
        };
    }

    const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;
    let period = null;
    let frequency = 1;
    let time = null;
    let parsedDayOfWeek = null;
    let parsedDayOfMonth = null;

    // Try to detect pattern - check most specific patterns first
    if (minute.startsWith("*/")) {
        // Every X minutes: */X * * * *
        period = "minute";
        frequency = parseInt(minute.substring(2)) || 1;
    } else if (hour.startsWith("*/") && !minute.startsWith("*/") && minute !== "*") {
        // Every X hours: 0 */X * * *
        period = "hourly";
        frequency = parseInt(hour.substring(2)) || 1;
    } else if (dayOfMonth.startsWith("*/") && month === "*" && dayOfWeek === "*") {
        // Every X days: minute hour */X * *
        period = "daily";
        frequency = parseInt(dayOfMonth.substring(2)) || 1;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    } else if (month.startsWith("*/") && dayOfMonth !== "*" && dayOfWeek !== "*") {
        // Monthly pattern with frequency: minute hour dayOfMonth */X dayOfWeek
        period = "monthly";
        frequency = parseInt(month.substring(2)) || 1;
        parsedDayOfMonth = parseInt(dayOfMonth) || null;
        parsedDayOfWeek = parseInt(dayOfWeek) !== null ? parseInt(dayOfWeek) : null;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    } else if (month.startsWith("*/") && dayOfMonth !== "*" && dayOfWeek === "*") {
        // Monthly pattern with frequency: minute hour dayOfMonth */X *
        period = "monthly";
        frequency = parseInt(month.substring(2)) || 1;
        parsedDayOfMonth = parseInt(dayOfMonth) || null;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    } else if (dayOfWeek !== "*" && month === "*" && dayOfMonth === "*") {
        // Weekly pattern: minute hour * * dayOfWeek
        period = "weekly";
        frequency = 1; // Weekly frequency is harder to detect
        parsedDayOfWeek = parseInt(dayOfWeek) !== null ? parseInt(dayOfWeek) : null;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    } else if (dayOfMonth !== "*" && month === "*" && dayOfWeek === "*") {
        // Monthly on specific day: minute hour dayOfMonth * *
        period = "monthly";
        frequency = 1;
        parsedDayOfMonth = parseInt(dayOfMonth) || null;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    } else if (dayOfMonth === "*" && month === "*" && dayOfWeek === "*") {
        // Daily at specific time: minute hour * * * (most common pattern)
        period = "daily";
        frequency = 1;
        time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
    }

    return {
        period,
        frequency,
        time,
        dayOfWeek: parsedDayOfWeek,
        dayOfMonth: parsedDayOfMonth,
        timezone: "UTC", // Legacy cron expressions default to UTC
        customDailySchedule: {},
    };
}

function validateForm() {
    formErrors.value = {};

    // Section 1: Basic Info
    if (!ruleForm.value.name || ruleForm.value.name.trim() === "") {
        formErrors.value.name = "Rule name is required";
    }

    // Section 2: Rule Level
    if (!ruleForm.value.ruleLevel) {
        formErrors.value.ruleLevel = "Rule level is required";
    }

    // Section 2B: At least one scope filter required
    if (!ruleForm.value.scopeFilters || ruleForm.value.scopeFilters.length === 0) {
        formErrors.value.scopeFilters = "At least one scope filter is required";
    } else {
        // Validate that each scope filter has a value
        const invalidScopes = [];
        ruleForm.value.scopeFilters.forEach((scope, idx) => {
                valueType: typeof scope.value,
                isArray: Array.isArray(scope.value),
            });

            if (scope.type === "name_contains") {
                // Check if it's an array with at least one non-empty string
                if (!scope.value) {
                    invalidScopes.push({
                        index: idx,
                        type: scope.type,
                        label: "Name contains",
                        reason: "value is null/undefined",
                    });
                } else if (!Array.isArray(scope.value)) {
                    invalidScopes.push({
                        index: idx,
                        type: scope.type,
                        label: "Name contains",
                        reason: "value is not an array",
                        actualType: typeof scope.value,
                    });
                } else if (scope.value.length === 0) {
                    invalidScopes.push({
                        index: idx,
                        type: scope.type,
                        label: "Name contains",
                        reason: "array is empty",
                    });
                } else {
                    // Check if all values are empty
                    const validValues = scope.value.filter((v) => v && typeof v === "string" && v.trim().length > 0);
                    if (validValues.length === 0) {
                        invalidScopes.push({
                            index: idx,
                            type: scope.type,
                            label: "Name contains",
                            reason: "all values are empty",
                            originalLength: scope.value.length,
                        });
                    }
                }
            } else if (scope.type === "ids") {
                // Chips component stores array, but we need to check if it's empty
                if (Array.isArray(scope.value)) {
                    const filtered = scope.value.filter((v) => v && String(v).trim().length > 0);
                    if (filtered.length === 0) {
                        const label =
                            ruleForm.value.ruleLevel === "ad"
                                ? "Ad ID"
                                : ruleForm.value.ruleLevel === "ad_set"
                                ? "Ad Set ID"
                                : "IDs";
                        invalidScopes.push({ index: idx, type: scope.type, label: label, reason: "value is empty" });
                    }
                } else if (typeof scope.value === "string" && scope.value.trim().length === 0) {
                    const label =
                        ruleForm.value.ruleLevel === "ad"
                            ? "Ad ID"
                            : ruleForm.value.ruleLevel === "ad_set"
                            ? "Ad Set ID"
                            : "IDs";
                    invalidScopes.push({ index: idx, type: scope.type, label: label, reason: "value is empty" });
                } else {
                    const ids = parseIds(scope.value);
                    if (ids.length === 0) {
                        const label =
                            ruleForm.value.ruleLevel === "ad"
                                ? "Ad ID"
                                : ruleForm.value.ruleLevel === "ad_set"
                                ? "Ad Set ID"
                                : "IDs";
                        invalidScopes.push({
                            index: idx,
                            type: scope.type,
                            label: label,
                            reason: "no valid IDs parsed",
                        });
                    }
                }
            }
        });
        if (invalidScopes.length > 0) {
            const labels = invalidScopes.map((s) => s.label).join(", ");
            const nameContainsIssue = invalidScopes.find((s) => s.type === "name_contains");
            if (nameContainsIssue) {
                formErrors.value.scopeFilters = `The "Name contains" filter requires at least one keyword. Please type a keyword and press Enter to add it.`;
            } else {
                formErrors.value.scopeFilters = `The following scope filter(s) are missing values: ${labels}. Please fill in all required fields.`;
            }
        }
    }

    // Section 3: Time Range
    if (!ruleForm.value.timeRangeUnit) {
        formErrors.value.timeRangeUnit = "Time unit is required";
    }
    if (!ruleForm.value.timeRangeAmount || ruleForm.value.timeRangeAmount < 1) {
        formErrors.value.timeRangeAmount = "Time amount is required and must be at least 1";
    }

    // Section 6: Schedule
    if (!validateSchedule()) {
        // Errors already in scheduleFormErrors
    }

    return Object.keys(formErrors.value).length === 0 && Object.keys(scheduleFormErrors.value).length === 0;
}

async function saveRule() {
    if (!selectedAccount.value) {
        toast.add({
            severity: "warn",
            summary: "Warning",
            detail: "Please select an ad account first",
            life: 3000,
        });
        return;
    }

    // Validate all form sections
    if (!validateForm()) {
        // Build detailed error message
        const errors = [];
        if (formErrors.value.name) errors.push(`Name: ${formErrors.value.name}`);
        if (formErrors.value.ruleLevel) errors.push(`Rule Level: ${formErrors.value.ruleLevel}`);
        if (formErrors.value.scopeFilters) errors.push(`Scope Filters: ${formErrors.value.scopeFilters}`);
        if (formErrors.value.timeRangeUnit) errors.push(`Time Unit: ${formErrors.value.timeRangeUnit}`);
        if (formErrors.value.timeRangeAmount) errors.push(`Time Amount: ${formErrors.value.timeRangeAmount}`);
        if (scheduleFormErrors.value.period) errors.push(`Schedule Period: ${scheduleFormErrors.value.period}`);
        if (scheduleFormErrors.value.frequency)
            errors.push(`Schedule Frequency: ${scheduleFormErrors.value.frequency}`);
        if (scheduleFormErrors.value.time) errors.push(`Schedule Time: ${scheduleFormErrors.value.time}`);
        if (scheduleFormErrors.value.dayOfWeek) errors.push(`Day of Week: ${scheduleFormErrors.value.dayOfWeek}`);
        if (scheduleFormErrors.value.dayOfMonth) errors.push(`Day of Month: ${scheduleFormErrors.value.dayOfMonth}`);

        const errorMessage = errors.length > 0 ? errors.join("; ") : "Please fix all form errors";

        toast.add({
            severity: "warn",
            summary: "Validation Error",
            detail: errorMessage,
            life: 6000,
        });
            scopeFilters: ruleForm.value.scopeFilters,
            timeRangeUnit: ruleForm.value.timeRangeUnit,
            timeRangeAmount: ruleForm.value.timeRangeAmount,
            schedulePeriod: ruleForm.value.schedulePeriod,
            scheduleFrequency: ruleForm.value.scheduleFrequency,
        });
        return;
    }

    // Build cron expression from schedule fields
    const cronExpression = buildCronExpression();
    // Allow null/empty cron expression when period is "none"
    if (ruleForm.value.schedulePeriod && ruleForm.value.schedulePeriod !== "none" && !cronExpression) {
        toast.add({
            severity: "warn",
            summary: "Validation Error",
            detail: "Invalid schedule configuration",
            life: 3000,
        });
        return;
    }

    // Build scope filters object
    const scopeObject = {};

    ruleForm.value.scopeFilters.forEach((scope, idx) => {

        if (scope.type === "name_contains") {
            // Chips component stores array of strings

            if (Array.isArray(scope.value) && scope.value.length > 0) {
                const filtered = scope.value.filter((v) => v && v.trim().length > 0);
                if (filtered.length > 0) {
                    scopeObject.name_contains = filtered;
                }
            } else if (typeof scope.value === "string" && scope.value.trim().length > 0) {
                // Fallback in case it's stored as string
                scopeObject.name_contains = [scope.value.trim()];
            } else {
            }
        } else if (scope.type === "ids") {
            // Chips component stores array of strings
            if (Array.isArray(scope.value) && scope.value.length > 0) {
                const filtered = scope.value.filter((v) => v && v.trim().length > 0);
                if (filtered.length > 0) {
                    scopeObject.ids = filtered;
                }
            } else if (typeof scope.value === "string" && scope.value.trim().length > 0) {
                // Fallback: handle comma-separated string
                const ids = parseIds(scope.value);
                if (ids.length > 0) {
                    scopeObject.ids = ids;
                }
            }
        } else if (scope.type === "campaign_name_contains") {
            // Chips component stores array of strings
            if (Array.isArray(scope.value) && scope.value.length > 0) {
                const filtered = scope.value.filter((v) => v && v.trim().length > 0);
                if (filtered.length > 0) {
                    scopeObject.campaign_name_contains = filtered;
                }
            } else if (typeof scope.value === "string" && scope.value.trim().length > 0) {
                scopeObject.campaign_name_contains = [scope.value.trim()];
            }
        } else if (scope.type === "campaign_ids") {
            // Chips component stores array of strings
            if (Array.isArray(scope.value) && scope.value.length > 0) {
                const filtered = scope.value.filter((v) => v && v.trim().length > 0);
                if (filtered.length > 0) {
                    scopeObject.campaign_ids = filtered;
                }
            } else if (typeof scope.value === "string" && scope.value.trim().length > 0) {
                // Fallback: handle comma-separated string
                const ids = parseIds(scope.value);
                if (ids.length > 0) {
                    scopeObject.campaign_ids = ids;
                }
            }
        }
    });

    // Debug: Log scope filters being saved

    // Build conditions JSON
    const conditionsJSON = {
        rule_level: ruleForm.value.ruleLevel,
        time_range: {
            unit: ruleForm.value.timeRangeUnit,
            amount: ruleForm.value.timeRangeAmount,
            exclude_today: ruleForm.value.excludeToday,
        },
        conditions: ruleForm.value.conditions.map((c) => ({
            field: c.field,
            operator: c.operator,
            value: c.value,
        })),
        ...scopeObject,
    };

    // Build actions JSON
    const actionsJSON = {
        actions: ruleForm.value.actions.map((a) => {
            const action = { type: a.type };
            if (a.type === "set_status") {
                action.status = a.status;
            } else if (a.type === "adjust_daily_budget") {
                action.direction = a.direction;
                action.percent = a.percent;
                if (a.minCap !== null && a.minCap !== undefined) action.min_cap = a.minCap;
                if (a.maxCap !== null && a.maxCap !== undefined) action.max_cap = a.maxCap;
            } else if (a.type === "send_notification") {
                // No additional fields needed for send_notification
            }
            // Include sendSlackNotification (default to true if not set, always true for send_notification)
            if (a.type === "send_notification") {
                action.send_slack_notification = true;
            } else {
                action.send_slack_notification = a.sendSlackNotification !== undefined ? a.sendSlackNotification : true;
            }
            return action;
        }),
    };

    saving.value = true;
    try {
        const ruleData = {
            name: ruleForm.value.name,
            description: ruleForm.value.description,
            schedule_cron: cronExpression,
            enabled: ruleForm.value.enabled,
            conditions: conditionsJSON,
            actions: actionsJSON,
            ad_account_id: selectedAccount.value.id,
        };

        // Debug: Log what's being saved

        if (editingRule.value) {
            await updateRule(editingRule.value.id, ruleData);
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
        closeDialog();
        await loadRules();
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: error.message || "Failed to save rule",
            life: 5000,
        });
    } finally {
        saving.value = false;
    }
}

function confirmDelete(rule) {
    confirm.require({
        message: `Are you sure you want to delete "${rule.name}"?`,
        header: "Confirm Delete",
        icon: "pi pi-exclamation-triangle",
        accept: async () => {
            try {
                await deleteRule(rule.id);
                toast.add({
                    severity: "success",
                    summary: "Success",
                    detail: "Rule deleted successfully",
                    life: 3000,
                });
                await loadRules();
            } catch (error) {
                toast.add({
                    severity: "error",
                    summary: "Error",
                    detail: "Failed to delete rule",
                    life: 5000,
                });
            }
        },
    });
}

async function testRule(ruleId) {
    testingRuleId.value = ruleId;
    try {
        const result = await testRuleApi(ruleId);
        toast.add({
            severity: result.decision === "proceed" ? "success" : "info",
            summary: "Rule Test Complete",
            detail: result.message || "Rule test completed",
            life: 5000,
        });
        // Reload rules and logs to show updated information
        await loadRules();
        // If viewing logs for this rule, refresh them
        if (editingRule.value?.id === ruleId) {
            await viewLogs(ruleId);
        }
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: error.message || "Failed to test rule",
            life: 5000,
        });
    } finally {
        testingRuleId.value = null;
    }
}

const currentRuleForLogs = ref(null);

async function viewLogs(ruleId) {
    showLogsDialog.value = true;
    loadingLogs.value = true;
    try {
        // Store the rule ID for reference in downloads
        currentRuleForLogs.value = rules.value.find((r) => r.id === ruleId) || null;
        logs.value = await getRuleLogs(ruleId);
    } catch (error) {
        toast.add({
            severity: "error",
            summary: "Error",
            detail: "Failed to load logs",
            life: 5000,
        });
    } finally {
        loadingLogs.value = false;
    }
}

function confirmDeleteLog(log) {
    confirm.require({
        message: `Are you sure you want to delete this log entry? This will remove the log from the database. Note: Any downloaded files on your computer will not be deleted.`,
        header: "Confirm Delete",
        icon: "pi pi-exclamation-triangle",
        accept: async () => {
            try {
                if (!currentRuleForLogs.value) {
                    toast.add({
                        severity: "error",
                        summary: "Error",
                        detail: "Cannot delete: Rule context missing",
                        life: 3000,
                    });
                    return;
                }
                await deleteRuleLog(currentRuleForLogs.value.id, log.id);
                toast.add({
                    severity: "success",
                    summary: "Success",
                    detail: "Log entry deleted successfully",
                    life: 3000,
                });
                // Reload logs
                await viewLogs(currentRuleForLogs.value.id);
            } catch (error) {
                toast.add({
                    severity: "error",
                    summary: "Error",
                    detail: error.message || "Failed to delete log entry",
                    life: 3000,
                });
            }
        },
    });
}

function showLogDetails(log) {
    selectedLogDetails.value = log;
    showLogDetailsDialog.value = true;
}

function downloadLogDetails(log) {
    if (!log || !log.details) {
        toast.add({
            severity: "warn",
            summary: "Warning",
            detail: "No detailed log data available",
            life: 3000,
        });
        return;
    }

    // Format log details for download
    const ruleInfo = currentRuleForLogs.value || editingRule.value;
    const logData = {
        rule_id: ruleInfo?.id || "N/A",
        rule_name: ruleInfo?.name || "N/A",
        log_id: log.id,
        timestamp: log.created_at,
        status: log.status,
        message: log.message,
        details: log.details,
    };

    // Create formatted text content
    let content = `RULE EXECUTION LOG REPORT\n`;
    content += `==========================================\n\n`;
    content += `Rule ID: ${logData.rule_id}\n`;
    content += `Rule Name: ${logData.rule_name}\n`;
    content += `Log ID: ${logData.log_id}\n`;
    content += `Timestamp: ${formatDate(logData.timestamp)}\n`;
    content += `Status: ${logData.status.toUpperCase()}\n`;
    content += `Message: ${logData.message}\n\n`;

    const details = logData.details;

    // Decision
    if (details.decision) {
        content += `DECISION: ${details.decision.toUpperCase()}\n`;
        content += `==========================================\n\n`;
    }

    // Summary
    if (details.items_checked !== undefined) {
        content += `SUMMARY\n`;
        content += `------------------------------------------\n`;
        content += `Items Checked: ${details.items_checked}\n`;
        if (details.items_meeting_conditions_count !== undefined) {
            content += `Items Meeting Conditions: ${details.items_meeting_conditions_count}\n`;
        }
        content += `\n`;
    }

    // Rule Configuration
    const hasScopeFilters = details.scope_filters || details.name_contains || details.ids;
    if (
        details.rule_level ||
        hasScopeFilters ||
        details.time_range ||
        (details.conditions && details.conditions.length > 0)
    ) {
        content += `RULE CONFIGURATION\n`;
        content += `------------------------------------------\n`;
        if (details.rule_level) {
            content += `Rule Level: ${details.rule_level}\n`;
        }

        // Build scope filters object - check both scope_filters key and individual keys
        const scopeFilters = details.scope_filters || {};
        if (details.name_contains && !scopeFilters.name_contains) {
            scopeFilters.name_contains = details.name_contains;
        }
        if (details.ids && !scopeFilters.ids) {
            scopeFilters.ids = details.ids;
        }

        if (Object.keys(scopeFilters).length > 0) {
            content += `Scope Filters: ${JSON.stringify(scopeFilters, null, 2)}\n`;
        } else {
            content += `Scope Filters: {}\n`;
        }

        if (details.time_range) {
            content += `Time Range: ${JSON.stringify(details.time_range, null, 2)}\n`;
        }

        // Show conditions configuration
        if (details.conditions && Array.isArray(details.conditions) && details.conditions.length > 0) {
            content += `Conditions Configuration:\n`;
            details.conditions.forEach((cond, idx) => {
                content += `  Condition ${idx + 1}: ${cond.field} ${cond.operator} ${cond.value}\n`;
            });
            content += `\n`;
        }

        content += `\n`;
    }

    // Data Fetch Summary
    if (details.data_fetch) {
        content += `DATA FETCH SUMMARY\n`;
        content += `------------------------------------------\n`;
        content += `Total Items Fetched: ${details.data_fetch.total_items || 0}\n`;
        if (details.data_fetch.items && details.data_fetch.items.length > 0) {
            content += `\nSample Items:\n`;
            details.data_fetch.items.slice(0, 10).forEach((item, idx) => {
                content += `  ${idx + 1}. ${item.name || "N/A"} (ID: ${item.id})\n`;
            });
            if (details.data_fetch.total_items > 10) {
                content += `  ... and ${details.data_fetch.total_items - 10} more items\n`;
            }
        }
        content += `\n`;
    }

    // Filtered Items
    if (details.filtered_data && details.filtered_data.length > 0) {
        content += `FILTERED ITEMS (${details.filtered_data.length})\n`;
        content += `------------------------------------------\n`;
        details.filtered_data.forEach((item, idx) => {
            content += `${idx + 1}. ${item.name || "N/A"}\n`;
            content += `   ID: ${item.id}\n`;
            content += `   Status: ${item.status || "N/A"}\n`;
            content += `   Effective Status: ${item.effective_status || "N/A"}\n`;
            content += `\n`;
        });
    }

    // Condition Evaluations
    if (details.evaluations && details.evaluations.length > 0) {
        content += `CONDITION EVALUATIONS\n`;
        content += `==========================================\n\n`;

        details.evaluations.forEach((evaluation, idx) => {
            content += `ITEM ${idx + 1}: ${evaluation.item_name} (ID: ${evaluation.item_id})\n`;
            content += `------------------------------------------\n`;

            if (evaluation.conditions_evaluated && evaluation.conditions_evaluated.length > 0) {
                evaluation.conditions_evaluated.forEach((cond, condIdx) => {
                    const status = cond.passed ? "✓ PASS" : "✗ FAIL";
                    content += `  Condition ${condIdx + 1}: ${status}\n`;
                    content += `    Field: ${cond.field}\n`;
                    content += `    Operator: ${cond.operator}\n`;
                    content += `    Expected Value: ${cond.expected_value}\n`;
                    content += `    Actual Value: ${
                        cond.actual_value !== null && cond.actual_value !== undefined ? cond.actual_value : "N/A"
                    }\n`;
                    content += `\n`;
                });
            }

            content += `  Overall Result: ${
                evaluation.all_conditions_met ? "✓ ALL CONDITIONS MET" : "✗ CONDITIONS NOT MET"
            }\n`;
            content += `\n\n`;
        });
    }

    // Items Meeting Conditions
    if (details.items_meeting_conditions && details.items_meeting_conditions.length > 0) {
        content += `ITEMS MEETING ALL CONDITIONS (${details.items_meeting_conditions.length})\n`;
        content += `------------------------------------------\n`;
        details.items_meeting_conditions.forEach((item, idx) => {
            content += `${idx + 1}. ${item.name || "N/A"} (ID: ${item.id})\n`;
        });
        content += `\n`;
    }

    // Actions Executed
    if (details.actions_executed && details.actions_executed.length > 0) {
        content += `ACTIONS EXECUTED (${details.actions_executed.length})\n`;
        content += `==========================================\n\n`;
        details.actions_executed.forEach((action, idx) => {
            content += `ACTION ${idx + 1}\n`;
            content += `------------------------------------------\n`;
            content += `Item: ${action.item_name || "N/A"} (ID: ${action.item_id})\n`;
            content += `Action Type: ${action.action_type}\n`;
            content += `Status: ${action.success ? "SUCCESS" : "FAILED"}\n`;
            content += `Message: ${action.message}\n`;
            if (action.old_budget !== undefined) {
                content += `Old Budget: $${action.old_budget.toFixed(2)}\n`;
            }
            if (action.new_budget !== undefined) {
                content += `New Budget: $${action.new_budget.toFixed(2)}\n`;
            }
            if (action.error) {
                content += `Error: ${action.error}\n`;
            }
            content += `\n`;
        });
    }

    // Conditions Configuration
    if (details.conditions && details.conditions.length > 0) {
        content += `CONDITIONS CONFIGURATION\n`;
        content += `------------------------------------------\n`;
        details.conditions.forEach((cond, idx) => {
            content += `Condition ${idx + 1}:\n`;
            content += `  Field: ${cond.field}\n`;
            content += `  Operator: ${cond.operator}\n`;
            content += `  Value: ${cond.value}\n`;
            content += `\n`;
        });
    }

    // Error Information
    if (details.error) {
        content += `ERROR INFORMATION\n`;
        content += `------------------------------------------\n`;
        content += `${details.error}\n\n`;
    }

    // Download as file
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `rule-log-${logData.log_id}-${new Date(logData.timestamp).toISOString().split("T")[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    toast.add({
        severity: "success",
        summary: "Download Started",
        detail: "Detailed log file is being downloaded",
        life: 3000,
    });
}

function getTimezoneFromSchedule(scheduleCron) {
    if (!scheduleCron) return null;
    try {
        const parsed = JSON.parse(scheduleCron);
        // All schedule types now support timezone in JSON format
        if (parsed.timezone) {
            return parsed.timezone;
        }
    } catch (e) {
        // Not JSON, return null (legacy format defaults to UTC)
    }
    return null;
}

function formatDateWithTimezone(date, scheduleCron) {
    if (!date) return "Never";
    const timezone = getTimezoneFromSchedule(scheduleCron);
    const dateObj = new Date(date);

    if (timezone) {
        // Format with timezone information - date is stored in UTC, display in schedule's timezone
        const options = {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            timeZone: timezone,
            hour12: false,
        };
        const formatted = dateObj.toLocaleString("en-US", options);
        // Extract timezone abbreviation or use the timezone name
        const tzAbbr =
            new Intl.DateTimeFormat("en-US", {
                timeZone: timezone,
                timeZoneName: "short",
            })
                .formatToParts(dateObj)
                .find((part) => part.type === "timeZoneName")?.value || timezone;
        return `${formatted} (${tzAbbr})`;
    } else {
        // Default formatting without timezone
        return dateObj.toLocaleString();
    }
}

function formatSchedule(scheduleCron) {
    if (!scheduleCron) return "Manual only";

    let cronExpr = scheduleCron;
    let timezone = "UTC";

    // Check if it's a JSON-wrapped schedule (all schedule types now support timezone)
    try {
        const parsed = JSON.parse(scheduleCron);

        // Handle custom daily schedule
        if (parsed.type === "custom_daily" && parsed.schedule) {
            const schedule = parsed.schedule;
            timezone = parsed.timezone || "UTC";

            // Build human-readable schedule
            const scheduleParts = [];
            const sortedDays = Object.keys(schedule)
                .map(Number)
                .sort((a, b) => a - b);

            for (const dayNum of sortedDays) {
                const dayName = weekDays.find((d) => d.value === dayNum)?.label || `Day ${dayNum}`;
                const time = schedule[dayNum.toString()];
                scheduleParts.push(`${dayName} at ${time}`);
            }

            if (scheduleParts.length === 0) {
                return "No schedule set";
            }

            const scheduleText = scheduleParts.join(", ");
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }

        // Handle other JSON-wrapped schedule types (daily, weekly, monthly, etc.)
        if (parsed.type && parsed.cron) {
            cronExpr = parsed.cron;
            timezone = parsed.timezone || "UTC";
        }
    } catch (e) {
        // Not JSON, use as-is (legacy format)
    }

    // Try to parse as regular cron expression
    const parts = cronExpr.trim().split(/\s+/);
    if (parts.length === 5) {
        const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;

        // Every X minutes
        if (minute.startsWith("*/")) {
            const freq = minute.substring(2);
            const scheduleText = `Every ${freq} minute${freq !== "1" ? "s" : ""}`;
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }

        // Every X hours
        if (hour.startsWith("*/") && minute !== "*" && !minute.startsWith("*/")) {
            const freq = hour.substring(2);
            const scheduleText = `Every ${freq} hour${freq !== "1" ? "s" : ""} at :${minute.padStart(2, "0")}`;
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }

        // Daily at specific time
        if (dayOfMonth === "*" && month === "*" && dayOfWeek === "*" && hour !== "*" && minute !== "*") {
            const time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
            if (dayOfMonth.startsWith("*/")) {
                const freq = dayOfMonth.substring(2);
                const scheduleText = `Every ${freq} day${freq !== "1" ? "s" : ""} at ${time}`;
                return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
            }
            const scheduleText = `Daily at ${time}`;
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }

        // Weekly on specific day
        if (dayOfWeek !== "*" && month === "*" && dayOfMonth === "*" && hour !== "*" && minute !== "*") {
            const dayName = weekDays.find((d) => d.value === parseInt(dayOfWeek))?.label || `Day ${dayOfWeek}`;
            const time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
            const scheduleText = `Every ${dayName} at ${time}`;
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }

        // Monthly on specific day
        if (dayOfMonth !== "*" && month === "*" && dayOfWeek === "*" && hour !== "*" && minute !== "*") {
            const time = `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
            let scheduleText;
            if (month.startsWith("*/")) {
                const freq = month.substring(2);
                scheduleText = `Every ${freq} month${freq !== "1" ? "s" : ""} on day ${dayOfMonth} at ${time}`;
            } else {
                scheduleText = `Monthly on day ${dayOfMonth} at ${time}`;
            }
            return timezone !== "UTC" ? `${scheduleText} (${timezone})` : scheduleText;
        }
    }

    // Fallback: return the cron expression as-is
    return scheduleCron;
}

function getStatusSeverity(status) {
    const map = {
        success: "success",
        error: "danger",
        skipped: "secondary",
    };
    return map[status] || "secondary";
}
</script>

<style scoped>
.meta-campaigns {
    max-width: 1400px;
    margin: 0 auto;
}

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
}

.page-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
}

.header-actions {
    display: flex;
    gap: 1rem;
}

.ad-accounts-section {
    margin-bottom: 3rem;
}

.campaigns-toggle-section {
    margin-top: 1rem;
    margin-bottom: 2rem;
}

.campaigns-toggle-button {
    width: 100%;
    justify-content: flex-start;
}

.campaigns-section {
    margin-top: 3rem;
    margin-bottom: 2rem;
    padding: 1.5rem;
    background-color: #ffffff;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.campaigns-section .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.campaigns-section .header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.campaigns-section .header-left h2 {
    margin: 0;
    font-size: 1rem;
    font-weight: 400;
    color: #1f2937;
}

.campaigns-section .header-left h2 .view-prefix {
    font-weight: 600;
    color: #6b7280;
    margin-right: 0.5rem;
}

.campaigns-section .back-button {
    margin-right: 0.5rem;
}

.clickable-row {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: #2563eb;
}

.clickable-row:hover {
    text-decoration: underline;
}


.campaigns-table {
    margin-top: 1rem;
}

.rules-section {
    margin-bottom: 3rem;
}

.ad-accounts-section h2,
.rules-section h2 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 1rem;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.accounts-table,
.rules-table {
    background: white;
    border-radius: 8px;
    overflow: hidden;
}

.name-column {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.name-text {
    font-weight: 600;
    color: #1f2937;
}

.description-text {
    font-size: 0.875rem;
    color: #6b7280;
    line-height: 1.4;
}

.run-time-text {
    font-size: 0.875rem;
}

.action-buttons {
    display: flex;
    gap: 0.5rem;
}

.form-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
}

.field {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 0;
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
}

.field label {
    font-weight: 600;
    color: #374151;
}

.field small {
    color: #6b7280;
    font-size: 0.875rem;
}

.access-token-field :deep(.p-password-input),
.access-token-field :deep(.p-inputtext) {
    min-height: 80px;
    font-size: 0.9rem;
    padding: 0.75rem;
}

.checkbox-field {
    flex-direction: row;
    align-items: center;
}

.connection-status-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.connection-status-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.connection-status-icon {
    font-size: 1.25rem;
}

.connection-status-icon.success {
    color: #22c55e;
}

.connection-status-icon.error {
    color: #ef4444;
}

.connection-status-icon.unknown {
    color: #6b7280;
}

.connection-status-text {
    font-weight: 500;
}

.connection-last-checked {
    margin-left: 1.75rem;
}

.checkbox-container {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.checkbox-label {
    white-space: nowrap;
    margin: 0;
    font-weight: 600;
    color: #374151;
}

.form-section {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.5rem;
    background-color: #f9fafb;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
    box-sizing: border-box;
}

.scheduling-section {
    margin-top: 1rem;
}

.subsection {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
}

.subsection:first-child {
    margin-top: 0;
    padding-top: 0;
    border-top: none;
}

.subsection-title {
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
    margin: 0 0 1rem 0;
}

.section-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 1.5rem 0;
}

.empty-scope,
.empty-message {
    padding: 1rem;
    background-color: #f3f4f6;
    border-radius: 6px;
    color: #6b7280;
    text-align: center;
    margin-bottom: 1rem;
}

.scope-filters-list,
.conditions-list,
.actions-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.scope-filter-item,
.condition-item,
.action-item {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 1rem;
    background-color: white;
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
    box-sizing: border-box;
}

.scope-filter-header,
.condition-header,
.action-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e5e7eb;
}

.scope-filter-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
}

.condition-fields,
.action-fields {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    max-width: 100%;
    overflow-x: hidden;
}

.rule-builder-dialog :deep(.p-dialog) {
    max-width: 900px;
    width: 90vw;
}

.rule-builder-dialog :deep(.p-dialog-content) {
    max-height: calc(90vh - 150px);
    overflow-y: auto;
    overflow-x: hidden;
    word-wrap: break-word;
}

.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 1rem 0;
}

.p-error {
    color: #ef4444;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

.p-text-secondary {
    color: #6b7280;
    font-size: 0.875rem;
}

.form-section {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.5rem;
    background-color: #f9fafb;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
    box-sizing: border-box;
}

.scheduling-section {
    margin-top: 1rem;
}

.subsection {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
}

.subsection:first-child {
    margin-top: 0;
    padding-top: 0;
    border-top: none;
}

.subsection-title {
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
    margin: 0 0 1rem 0;
}

.empty-scope,
.empty-message {
    padding: 1rem;
    background-color: #f3f4f6;
    border-radius: 6px;
    color: #6b7280;
    text-align: center;
    margin-bottom: 1rem;
}

.scope-filters-list,
.conditions-list,
.actions-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.scope-filter-item,
.condition-item,
.action-item {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 1rem;
    background-color: white;
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
    box-sizing: border-box;
}

.scope-filter-header,
.condition-header,
.action-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e5e7eb;
}

.scope-filter-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
}

.condition-fields,
.action-fields {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    max-width: 100%;
    overflow-x: hidden;
}

.rule-builder-dialog :deep(.p-dialog-content) {
    max-height: calc(90vh - 150px);
    overflow-y: auto;
    overflow-x: hidden;
    word-wrap: break-word;
}

.field-label {
    margin: 0;
    font-weight: 600;
    color: #374151;
}

/* Prevent horizontal overflow in input fields and components */
.rule-builder-dialog :deep(.p-inputtext),
.rule-builder-dialog :deep(.p-inputnumber),
.rule-builder-dialog :deep(.p-select),
.rule-builder-dialog :deep(.p-chips),
.rule-builder-dialog :deep(.p-textarea) {
    max-width: 100%;
    box-sizing: border-box;
}

.rule-builder-dialog :deep(.p-chips .p-chips-token) {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.log-details-content {
    max-height: calc(90vh - 200px);
    overflow-y: auto;
    overflow-x: hidden;
    word-wrap: break-word;
    max-width: 100%;
}

.log-section {
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e5e7eb;
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
}

.log-section:last-child {
    border-bottom: none;
}

.log-section h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #1f2937;
}

.log-section h5 {
    margin: 1rem 0 0.5rem 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: #374151;
}

.evaluation-item {
    margin-bottom: 1.5rem;
    padding: 1rem;
    background-color: #f9fafb;
    border-radius: 6px;
}

.condition-result {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.5rem 0;
}

.condition-text {
    font-family: monospace;
    font-size: 0.9rem;
    word-wrap: break-word;
    overflow-wrap: break-word;
    max-width: 100%;
}

.custom-daily-schedule {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 0.5rem;
}

.custom-daily-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background-color: #fff;
}

.day-checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 120px;
}

.day-label {
    font-weight: 500;
    color: #374151;
    cursor: pointer;
    user-select: none;
}

.time-input {
    flex: 1;
    max-width: 150px;
}

.time-input:disabled {
    background-color: #f3f4f6;
    color: #9ca3af;
    cursor: not-allowed;
}

.condition-overall {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.error-section pre {
    background-color: #fee2e2;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: hidden;
    overflow-y: auto;
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-all;
    white-space: pre-wrap;
    max-width: 100%;
    color: #991b1b;
}

.logs-dialog :deep(.p-dialog),
.log-details-dialog :deep(.p-dialog) {
    max-width: 900px;
    width: 90vw;
}

/* Confirmation dialog styling - PrimeVue uses .p-confirm-dialog wrapper */
:deep(.p-confirm-dialog),
:deep(.p-confirm-dialog .p-dialog),
:deep(.p-confirm-dialog-wrapper .p-dialog) {
    max-width: 900px !important;
    width: 90vw !important;
}

/* Confirmation dialog content styling */
:deep(.p-confirm-dialog .p-dialog-content),
:deep(.p-confirm-dialog .p-dialog-message) {
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
}

.logs-dialog :deep(.p-dialog-content),
.log-details-dialog :deep(.p-dialog-content) {
    max-height: calc(90vh - 150px);
    overflow-y: auto;
    overflow-x: hidden;
    word-wrap: break-word;
}

.logs-dialog,
.log-details-dialog {
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
}

.log-details {
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
}

/* Prevent DataTable overflow in logs dialogs */
.logs-dialog :deep(.p-datatable),
.log-details-dialog :deep(.p-datatable) {
    max-width: 100%;
    overflow-x: hidden;
    width: 100%;
}

.logs-dialog :deep(.p-datatable-wrapper),
.log-details-dialog :deep(.p-datatable-wrapper) {
    max-width: 100%;
    overflow-x: hidden;
    width: 100%;
}

.logs-dialog :deep(.p-datatable-table),
.log-details-dialog :deep(.p-datatable-table) {
    table-layout: fixed;
    width: 100%;
    max-width: 100%;
}

.logs-dialog :deep(.p-datatable-thead th),
.log-details-dialog :deep(.p-datatable-thead th) {
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: normal;
}

.logs-dialog :deep(.p-datatable-tbody td),
.log-details-dialog :deep(.p-datatable-tbody td) {
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-all;
    white-space: normal;
    max-width: 0;
    padding: 0.75rem;
    overflow: hidden;
}

.logs-dialog :deep(.p-datatable-tbody td .p-tag),
.log-details-dialog :deep(.p-datatable-tbody td .p-tag) {
    max-width: 100%;
    word-wrap: break-word;
    white-space: normal;
}

/* Target all cell content including text nodes */
.logs-dialog :deep(.p-datatable-tbody td *),
.log-details-dialog :deep(.p-datatable-tbody td *) {
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-all;
    max-width: 100%;
}

/* Error text in cells should wrap and break long URLs */
.error-text {
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-all;
    white-space: normal;
    max-width: 100%;
    display: inline-block;
}

/* Message text in logs table */
.message-text {
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-all;
    white-space: normal;
    max-width: 100%;
    display: inline-block;
}

/* Ensure the message column specifically wraps */
.logs-dialog :deep(.p-datatable-tbody tr td:nth-of-type(2)),
.log-details-dialog :deep(.p-datatable-tbody tr td:nth-of-type(2)) {
    word-break: break-all;
    overflow-wrap: anywhere;
    white-space: normal !important;
    max-width: 0;
}

.logs-table-wrapper {
    max-width: 100%;
    overflow-x: hidden;
    width: 100%;
    box-sizing: border-box;
}

.log-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.action-slack-notification {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid #e5e7eb;
}

.slack-notification-label {
    font-size: 0.875rem;
    color: #6b7280;
    font-weight: 500;
    margin: 0;
    cursor: pointer;
}

/* Global styles for PrimeVue ConfirmDialog (rendered at app level) */
</style>

<style>
/* Global styles for ConfirmDialog - not scoped since it's rendered outside component */
.p-confirm-dialog,
.p-confirm-dialog .p-dialog,
.p-confirm-dialog-wrapper .p-dialog {
    max-width: 900px !important;
    width: 90vw !important;
}

.p-confirm-dialog .p-dialog-content,
.p-confirm-dialog .p-dialog-message {
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
}
</style>
