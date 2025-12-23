<template>
    <Dialog
        :visible="modelValue"
        header="Log Details"
        :modal="true"
        :style="{ maxWidth: '900px', width: '90vw', maxHeight: '90vh' }"
        class="log-details-dialog"
        @update:visible="$emit('update:modelValue', $event)"
    >
        <div v-if="logDetails && logDetails.details" class="log-details">
            <div v-if="logDetails.details.decision" class="log-section">
                <h4>
                    Decision:
                    <Tag
                        :value="logDetails.details.decision.toUpperCase()"
                        :severity="logDetails.details.decision === 'proceed' ? 'success' : 'secondary'"
                    />
                </h4>
            </div>

            <div v-if="logDetails.details.items_checked !== undefined" class="log-section">
                <h4>Summary</h4>
                <p><strong>Items Checked:</strong> {{ logDetails.details.items_checked }}</p>
                <p v-if="logDetails.details.items_meeting_conditions_count !== undefined">
                    <strong>Items Meeting Conditions:</strong>
                    {{ logDetails.details.items_meeting_conditions_count }}
                </p>
            </div>

            <div
                v-if="logDetails.details.filtered_data && logDetails.details.filtered_data.length > 0"
                class="log-section"
            >
                <h4>Filtered Items ({{ logDetails.details.filtered_data.length }})</h4>
                <DataTable :value="logDetails.details.filtered_data" size="small">
                    <Column field="id" header="ID" />
                    <Column field="name" header="Name" />
                    <Column field="status" header="Status" />
                </DataTable>
            </div>

            <div
                v-if="logDetails.details.evaluations && logDetails.details.evaluations.length > 0"
                class="log-section"
            >
                <h4>Condition Evaluations</h4>
                <div
                    v-for="(evaluation, idx) in logDetails.details.evaluations"
                    :key="idx"
                    class="evaluation-item"
                >
                    <h5>{{ evaluation.item_name }} (ID: {{ evaluation.item_id }})</h5>
                    <div
                        v-for="(cond, condIdx) in evaluation.conditions_evaluated"
                        :key="condIdx"
                        class="condition-result"
                    >
                        <div class="condition-header">
                            <Tag
                                :value="cond.passed ? 'PASS' : 'FAIL'"
                                :severity="cond.passed ? 'success' : 'danger'"
                                class="condition-tag"
                            />
                            <span class="condition-text">
                                {{ cond.field }} {{ cond.operator }}
                                {{ cond.expected_expression ?? cond.expected_value }}
                            </span>
                        </div>
                        <div v-if="cond.threshold !== null && cond.threshold !== undefined" class="p-text-secondary condition-threshold">
                            <strong>Threshold:</strong> {{ cond.threshold }}
                        </div>
                        <div v-if="cond.time_range_used" class="p-text-secondary condition-time-range">
                            <strong>Time Range:</strong>
                            <span v-if="typeof cond.time_range_used === 'object' && cond.time_range_used !== null">
                                {{ formatTimeRange(cond.time_range_used) }}
                            </span>
                            <span v-else-if="cond.time_range_used === 'global'">
                                Global ({{ formatTimeRange(logDetails.details.time_range) }})
                            </span>
                            <span v-else>{{ cond.time_range_used }}</span>
                        </div>
                        <div class="p-text-secondary condition-compare-line">
                            Compared: actual =
                            {{
                                cond.actual_value !== null && cond.actual_value !== undefined
                                    ? cond.actual_value
                                    : 'N/A'
                            }}
                            {{ cond.operator }}
                            expected =
                            {{
                                cond.expected_value !== null && cond.expected_value !== undefined
                                    ? cond.expected_value
                                    : 'N/A'
                            }}
                        </div>
                        <!-- CPP Winning Days Breakdown -->
                        <div v-if="cond.cpp_winning_days_breakdown && cond.cpp_winning_days_breakdown.length > 0" class="cpp-winning-days-breakdown">
                            <strong>Daily CPP Breakdown ({{ cond.cpp_winning_days_total_days }} days):</strong>
                            <div class="daily-cpp-list">
                                <div
                                    v-for="(day, dayIdx) in cond.cpp_winning_days_breakdown"
                                    :key="dayIdx"
                                    :class="['daily-cpp-item', { 'winning': day.is_winning }]"
                                >
                                    <span class="date">{{ day.date }}:</span>
                                    <span class="cpp-value">
                                        CPP = ${{ formatNumber(day.cpp) }}
                                    </span>
                                    <span v-if="day.spend !== null && day.spend !== undefined" class="spend">
                                        (Spend: ${{ formatNumber(day.spend) }})
                                    </span>
                                    <Tag
                                        v-if="day.is_winning"
                                        value="WINNING"
                                        severity="success"
                                        class="winning-tag"
                                    />
                                </div>
                            </div>
                        </div>
                        <!-- Media Margin Volume Details (debug) -->
                        <div v-if="cond.calculation_details" class="calculation-details">
                            <div class="calculation-formula">
                                <strong>Formula:</strong> {{ cond.calculation_details.formula }}
                            </div>
                            <div class="calculation-breakdown">
                                <div>
                                    <strong>Purchase Value:</strong>
                                    ${{
                                        (cond.calculation_details.purchase_value ?? 0).toFixed
                                            ? cond.calculation_details.purchase_value.toFixed(2)
                                            : cond.calculation_details.purchase_value
                                    }}
                                    <span class="p-text-secondary"
                                        >(source: {{ cond.calculation_details.purchase_value_source }})</span
                                    >
                                </div>
                                <div>
                                    <strong>Spend:</strong>
                                    ${{
                                        (cond.calculation_details.spend ?? 0).toFixed
                                            ? cond.calculation_details.spend.toFixed(2)
                                            : cond.calculation_details.spend
                                    }}
                                </div>
                                <div><strong>Purchases:</strong> {{ cond.calculation_details.purchase_count }}</div>
                                <div
                                    v-if="
                                        cond.calculation_details.aov !== null &&
                                        cond.calculation_details.aov !== undefined
                                    "
                                >
                                    <strong>AOV:</strong> ${{ cond.calculation_details.aov.toFixed(2) }}
                                </div>
                                <div
                                    v-if="
                                        cond.calculation_details.cpp !== null &&
                                        cond.calculation_details.cpp !== undefined
                                    "
                                >
                                    <strong>CPP:</strong> ${{ cond.calculation_details.cpp.toFixed(2) }}
                                </div>
                                <div class="calculation-result">
                                    <strong>Result:</strong> ${{ cond.calculation_details.result.toFixed(2) }}
                                </div>
                                <div v-if="cond.calculation_details.note" class="p-text-secondary">
                                    {{ cond.calculation_details.note }}
                                </div>
                            </div>
                        </div>
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
                v-if="logDetails.details.actions_executed && logDetails.details.actions_executed.length > 0"
                class="log-section"
            >
                <h4>Actions Executed ({{ logDetails.details.actions_executed.length }})</h4>
                <DataTable :value="logDetails.details.actions_executed" size="small">
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
                        v-if="logDetails.details.actions_executed.some((a) => a.old_budget !== undefined)"
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
                        v-if="logDetails.details.actions_executed.some((a) => a.new_budget !== undefined)"
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
                        v-if="logDetails.details.actions_executed.some((a) => a.error)"
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

            <div v-if="logDetails.details.error" class="log-section error-section">
                <h4>Error</h4>
                <pre>{{ logDetails.details.error }}</pre>
            </div>

            <div
                v-if="
                    logDetails.details.rule_level ||
                    logDetails.details.scope_filters ||
                    logDetails.details.time_range
                "
                class="log-section"
            >
                <h4>Rule Configuration</h4>
                <p v-if="logDetails.details.rule_level">
                    <strong>Rule Level:</strong> {{ logDetails.details.rule_level }}
                </p>
                <p v-if="logDetails.details.scope_filters">
                    <strong>Scope Filters:</strong>
                    {{ JSON.stringify(logDetails.details.scope_filters, null, 2) }}
                </p>
                <p v-if="logDetails.details.time_range">
                    <strong>Time Range:</strong>
                    {{ JSON.stringify(logDetails.details.time_range, null, 2) }}
                </p>
            </div>

            <div v-if="logDetails.details.data_fetch" class="log-section">
                <h4>Data Fetch Summary</h4>
                <p>
                    <strong>Total Items Fetched:</strong>
                    {{ logDetails.details.data_fetch.total_items || 0 }}
                </p>
            </div>
        </div>
        <div v-else class="empty-message">
            <p>No detailed information available for this log entry.</p>
        </div>
        <template #footer>
            <Button label="Close" severity="secondary" @click="$emit('update:modelValue', false)" />
        </template>
    </Dialog>
</template>

<script setup>
import Dialog from 'primevue/dialog'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'

defineProps({
    modelValue: {
        type: Boolean,
        default: false,
    },
    logDetails: {
        type: Object,
        default: null,
    },
})

defineEmits(['update:modelValue'])

function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined) {
        return 'N/A'
    }
    const num = typeof value === 'number' ? value : parseFloat(value)
    if (isNaN(num)) {
        return 'N/A'
    }
    return num.toFixed(decimals)
}

function formatTimeRange(timeRange) {
    if (!timeRange || typeof timeRange !== 'object') {
        return 'N/A'
    }

    const unit = timeRange.unit || 'days'
    const amount = timeRange.amount || 1
    const excludeToday = timeRange.exclude_today !== undefined ? timeRange.exclude_today : true

    if (unit === 'today') {
        return 'Today only'
    }

    const unitLabel = unit === 'minutes' ? 'min' : unit === 'hours' ? 'hr' : 'day'
    const excludeText = excludeToday ? ' (excl. today)' : ''
    return `${amount} ${unitLabel}${amount !== 1 ? 's' : ''}${excludeText}`
}
</script>

<style scoped>
.log-details {
    max-width: 100%;
    overflow-x: hidden;
    word-wrap: break-word;
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
    margin: 0.5rem 0 0.25rem 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: #374151;
}

.evaluation-item {
    margin-bottom: 0.75rem;
    padding: 0.5rem;
    background-color: #f9fafb;
    border-radius: 6px;
}

.condition-result {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin: 0.25rem 0;
    padding: 0.5rem;
    background-color: #f9fafb;
    border-radius: 0.375rem;
    border-left: 3px solid #e5e7eb;
}

.condition-header {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 0;
}

.condition-tag {
    flex-shrink: 0;
}

.condition-text {
    font-family: monospace;
    font-size: 0.9rem;
    word-wrap: break-word;
    overflow-wrap: break-word;
    max-width: 100%;
}

.condition-threshold {
    font-size: 0.875rem;
    margin-top: 0.25rem;
    margin-bottom: 0.25rem;
    font-style: italic;
}

.condition-time-range {
    font-size: 0.875rem;
    margin-top: 0.25rem;
    margin-bottom: 0.25rem;
    font-style: italic;
}

.condition-compare-line {
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

.calculation-details {
    margin-top: 0.25rem;
    margin-bottom: 0;
    padding: 0.5rem;
    background-color: #ffffff;
    border-radius: 0.375rem;
    border: 1px solid #e5e7eb;
    font-size: 0.75rem;
}

.calculation-formula {
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e5e7eb;
    color: #374151;
    font-size: 0.7rem;
}

.calculation-breakdown {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.calculation-breakdown > div {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    color: #4b5563;
}

.calculation-result {
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid #e5e7eb;
    font-weight: 600;
    color: #1f2937;
}

.condition-overall {
    margin-top: 0.5rem;
    padding-top: 0.5rem;
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

.empty-message {
    padding: 2rem;
    text-align: center;
    color: #6b7280;
}

.error-text {
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-all;
    white-space: normal;
    max-width: 100%;
    display: inline-block;
}

.p-text-secondary {
    color: #6b7280;
    font-size: 0.875rem;
}

.cpp-winning-days-breakdown {
    margin-top: 1rem;
    padding: 1rem;
    background-color: #f9fafb;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
}

.cpp-winning-days-breakdown strong {
    display: block;
    margin-bottom: 0.75rem;
    color: #1f2937;
    font-size: 0.9rem;
}

.daily-cpp-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.daily-cpp-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background-color: white;
    border-radius: 4px;
    border: 1px solid #e5e7eb;
    font-size: 0.875rem;
}

.daily-cpp-item.winning {
    border-color: #10b981;
    background-color: #f0fdf4;
}

.daily-cpp-item .date {
    font-weight: 600;
    color: #374151;
    min-width: 100px;
}

.daily-cpp-item .cpp-value {
    color: #1f2937;
    font-weight: 500;
}

.daily-cpp-item .spend {
    color: #6b7280;
    font-size: 0.8rem;
}

.daily-cpp-item .winning-tag {
    margin-left: auto;
}
</style>

