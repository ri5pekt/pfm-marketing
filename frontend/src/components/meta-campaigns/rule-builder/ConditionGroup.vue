<template>
    <div class="condition-group">
        <div class="group-header">
            <span class="group-label">Group {{ groupIndex + 1 }}</span>
            <Button
                v-if="canDelete"
                icon="pi pi-times"
                severity="danger"
                text
                rounded
                size="small"
                @click="$emit('remove-group')"
                v-tooltip.top="'Remove Group'"
            />
        </div>

        <div class="conditions-list">
            <template v-for="(condition, idx) in group.conditions" :key="idx">
                <div v-if="idx > 0" class="and-connector">AND</div>

                <ConditionItem
                    :condition="condition"
                    :index="idx"
                    :available-condition-fields="availableConditionFields"
                    :operator-options="operatorOptions"
                    :status-options="statusOptions"
                    :available-special-values="availableSpecialValues"
                    :global-time-range="globalTimeRange"
                    @update="handleConditionUpdate(idx, $event)"
                    @remove="removeCondition(idx)"
                />
            </template>
        </div>

        <div class="add-condition-section">
            <Button
                label="Add Condition"
                icon="pi pi-plus"
                severity="secondary"
                outlined
                size="small"
                @click="addCondition"
            />
        </div>
    </div>
</template>

<script setup>
import Button from "primevue/button";
import ConditionItem from "./ConditionItem.vue";

const props = defineProps({
    group: { type: Object, required: true },
    groupIndex: { type: Number, required: true },
    canDelete: { type: Boolean, default: true },
    availableConditionFields: { type: Array, required: true },
    operatorOptions: { type: Array, required: true },
    statusOptions: { type: Array, required: true },
    availableSpecialValues: { type: Array, required: true },
    globalTimeRange: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["update-condition", "remove-condition", "add-condition", "remove-group"]);

function handleConditionUpdate(index, update) {
    emit("update-condition", { index, update });
}

function removeCondition(index) {
    emit("remove-condition", index);
}

function addCondition() {
    emit("add-condition");
}
</script>

<style scoped>
.condition-group {
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    padding: 1rem;
    background: #ffffff;
    margin-bottom: 1rem;
}

.group-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #e5e7eb;
}

.group-label {
    font-weight: 600;
    font-size: 0.9375rem;
    color: #374151;
}

.conditions-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.and-connector {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.25rem 0;
    font-size: 0.75rem;
    font-weight: 600;
    color: #6b7280;
}

.and-connector::before {
    content: "";
    flex: 1;
    height: 1px;
    background: #d1d5db;
    margin-right: 0.5rem;
}

.and-connector::after {
    content: "";
    flex: 1;
    height: 1px;
    background: #d1d5db;
    margin-left: 0.5rem;
}

.add-condition-section {
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px dashed #d1d5db;
}
</style>
