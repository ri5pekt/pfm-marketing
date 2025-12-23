<template>
    <div class="form-section">
        <h3 class="section-title">2. Level and Scope</h3>

        <!-- 2A: Rule Level -->
        <div class="subsection">
            <h4 class="subsection-title">2A. Rule Level</h4>
            <div class="field">
                <label>Rule Level *</label>
                <Select
                    :modelValue="modelValue.ruleLevel"
                    @update:modelValue="update('ruleLevel', $event)"
                    :options="ruleLevelOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select rule level"
                    class="w-full"
                    :class="{ 'p-invalid': errors.ruleLevel }"
                    @change="onRuleLevelChange"
                />
                <small v-if="errors.ruleLevel" class="p-error">{{ errors.ruleLevel }}</small>
            </div>
        </div>

        <!-- 2B: Scope Filters -->
        <div class="subsection">
            <h4 class="subsection-title">2B. Scope Filters</h4>
            <div v-if="modelValue.scopeFilters.length === 0" class="empty-scope">
                <p>No scope filters defined.</p>
            </div>
            <div v-else class="scope-filters-list">
                <div
                    v-for="(scope, index) in modelValue.scopeFilters"
                    :key="index"
                    class="scope-filter-item"
                >
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
                                :modelValue="scope.value"
                                @update:modelValue="updateScopeValue(index, $event)"
                                placeholder="Type keyword and press Enter to add"
                                class="w-full"
                                :class="{
                                    'p-invalid':
                                        errors.scopeFilters &&
                                        (!Array.isArray(scope.value) || scope.value.length === 0),
                                }"
                                @add="() => { if (errors.scopeFilters) emit('clearScopeError'); }"
                                @remove="() => {}"
                            />
                            <small
                                v-if="
                                    errors.scopeFilters &&
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
                                v-if="
                                    scope.value &&
                                    Array.isArray(scope.value) &&
                                    scope.value.length > 0
                                "
                                class="p-text-secondary mt-1 block"
                            >
                                Added keywords ({{ scope.value.length }}):
                                {{ scope.value.join(", ") }}
                            </small>
                        </div>
                        <!-- IDs -->
                        <div v-else-if="scope.type === 'ids'" class="field">
                            <label
                                >{{
                                    modelValue.ruleLevel === "ad"
                                        ? "Ad ID"
                                        : modelValue.ruleLevel === "ad_set"
                                        ? "Ad Set ID"
                                        : "IDs"
                                }}
                                *</label
                            >
                            <Chips
                                :modelValue="scope.value"
                                @update:modelValue="updateScopeValue(index, $event)"
                                placeholder="Type ID and press Enter to add"
                                class="w-full"
                                :class="{
                                    'p-invalid':
                                        errors.scopeFilters &&
                                        (!Array.isArray(scope.value) || scope.value.length === 0),
                                }"
                                @add="() => { if (errors.scopeFilters) emit('clearScopeError'); }"
                                @remove="() => {}"
                            />
                            <small
                                v-if="
                                    errors.scopeFilters &&
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
                                v-if="
                                    scope.value &&
                                    Array.isArray(scope.value) &&
                                    scope.value.length > 0
                                "
                                class="p-text-secondary mt-1 block"
                            >
                                Added IDs ({{ scope.value.length }}): {{ scope.value.join(", ") }}
                            </small>
                        </div>
                        <!-- Campaign Name contains -->
                        <div v-else-if="scope.type === 'campaign_name_contains'" class="field">
                            <label>Keywords *</label>
                            <Chips
                                :modelValue="scope.value"
                                @update:modelValue="updateScopeValue(index, $event)"
                                placeholder="Type keyword and press Enter to add"
                                class="w-full"
                                :class="{
                                    'p-invalid':
                                        errors.scopeFilters &&
                                        (!Array.isArray(scope.value) || scope.value.length === 0),
                                }"
                                @add="() => { if (errors.scopeFilters) emit('clearScopeError'); }"
                                @remove="() => {}"
                            />
                            <small
                                v-if="
                                    errors.scopeFilters &&
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
                                v-if="
                                    scope.value &&
                                    Array.isArray(scope.value) &&
                                    scope.value.length > 0
                                "
                                class="p-text-secondary mt-1 block"
                            >
                                Added keywords ({{ scope.value.length }}):
                                {{ scope.value.join(", ") }}
                            </small>
                        </div>
                        <!-- Campaign IDs -->
                        <div v-else-if="scope.type === 'campaign_ids'" class="field">
                            <label>Campaign IDs *</label>
                            <Chips
                                :modelValue="scope.value"
                                @update:modelValue="updateScopeValue(index, $event)"
                                placeholder="Type campaign ID and press Enter to add"
                                class="w-full"
                                :class="{
                                    'p-invalid':
                                        errors.scopeFilters &&
                                        (!Array.isArray(scope.value) || scope.value.length === 0),
                                }"
                                @add="() => { if (errors.scopeFilters) emit('clearScopeError'); }"
                                @remove="() => {}"
                            />
                            <small
                                v-if="
                                    errors.scopeFilters &&
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
                                v-if="
                                    scope.value &&
                                    Array.isArray(scope.value) &&
                                    scope.value.length > 0
                                "
                                class="p-text-secondary mt-1 block"
                            >
                                Added campaign IDs ({{ scope.value.length }}):
                                {{ scope.value.join(", ") }}
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
                    @click="$emit('openAddScopeDialog')"
                    :disabled="availableScopeTypes.length === 0"
                />
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from "vue";
import Select from "primevue/select";
import Button from "primevue/button";
import Chips from "primevue/chips";

const props = defineProps({
    modelValue: {
        type: Object,
        required: true,
    },
    errors: {
        type: Object,
        default: () => ({}),
    },
    availableScopeTypes: {
        type: Array,
        default: () => [],
    },
});

const emit = defineEmits(["update:modelValue", "openAddScopeDialog", "clearScopeError"]);

const ruleLevelOptions = [
    { label: "Ad", value: "ad" },
    { label: "Ad Set", value: "ad_set" },
    { label: "Campaign", value: "campaign" },
];

const scopeTypeOptions = [
    { label: "Name contains", value: "name_contains" },
    { label: "IDs", value: "ids" },
    { label: "Campaign Name contains", value: "campaign_name_contains" },
    { label: "Campaign IDs", value: "campaign_ids" },
];

function update(field, value) {
    emit("update:modelValue", {
        ...props.modelValue,
        [field]: value,
    });
}

function updateScopeValue(index, value) {
    const newScopeFilters = [...props.modelValue.scopeFilters];
    newScopeFilters[index] = {
        ...newScopeFilters[index],
        value,
    };
    update("scopeFilters", newScopeFilters);
}

function removeScopeFilter(index) {
    const newScopeFilters = [...props.modelValue.scopeFilters];
    newScopeFilters.splice(index, 1);
    update("scopeFilters", newScopeFilters);
}

function getScopeTypeLabel(type) {
    const option = scopeTypeOptions.find((opt) => opt.value === type);
    let label = option ? option.label : type;
    // Make IDs label dynamic based on rule level
    if (type === "ids") {
        if (props.modelValue.ruleLevel === "ad") {
            label = "Ad ID";
        } else if (props.modelValue.ruleLevel === "ad_set") {
            label = "Ad Set ID";
        }
    }
    return label;
}

function onRuleLevelChange() {
    emit("ruleLevelChanged");
}
</script>

<style scoped>
.form-section {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.5rem;
    background-color: #f9fafb;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}

.section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 1rem 0;
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

.field {
    margin-bottom: 1rem;
}

.field:last-child {
    margin-bottom: 0;
}

.field label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #374151;
}

.empty-scope {
    padding: 1rem;
    background-color: #f3f4f6;
    border-radius: 6px;
    color: #6b7280;
    text-align: center;
    margin-bottom: 1rem;
}

.scope-filters-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.scope-filter-item {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 1rem;
    background-color: white;
}

.scope-filter-header {
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

.block {
    display: block;
}

.mt-1 {
    margin-top: 0.25rem;
}

.mt-3 {
    margin-top: 1rem;
}
</style>

